import json
from pathlib import Path

from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from backend_src.core.security import hash_password
from backend_src.db import AsyncDBSession, Queries
from backend_src.models import AfdModerator
from .errors import SeedError


class SeedModerator(BaseModel):
    email: EmailStr = Field(max_length=255)
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    # Same rule as the pilot password
    password: str = Field(min_length=8)


class ModeratorSeedFile(BaseModel):
    moderators: list[SeedModerator]

    @field_validator("moderators")
    @classmethod
    def unique_emails(cls, moderators: list[SeedModerator]) -> list[SeedModerator]:
        seen: set[str] = set()
        for moderator in moderators:
            email = moderator.email.lower()
            if email in seen:
                raise ValueError(f"duplicate email {email}")
            seen.add(email)

        return moderators


class ModeratorSeedReport(BaseModel):
    created: list[str]
    skipped: list[str]


def _describe(error: ValidationError) -> str:
    # Only the location and the message, the input may be a password
    return "; ".join(
        f"{'.'.join(str(part) for part in issue['loc']) or 'file'}: {issue['msg']}" for issue in error.errors()
    )


def load_moderators(path: Path) -> list[SeedModerator]:
    """Profiles of the seed file; SeedError when it is missing or invalid."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SeedError(f"Seed file {path} not found, copy data/seed/moderators.example.json") from None
    except OSError as exc:
        raise SeedError(f"Seed file {path} cannot be read: {exc.strerror}") from None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SeedError(f"Seed file {path} is not valid JSON: line {exc.lineno}, column {exc.colno}") from None

    try:
        return ModeratorSeedFile.model_validate(data).moderators
    except ValidationError as exc:
        raise SeedError(f"Seed file {path} is invalid: {_describe(exc)}") from None


async def seed_moderators(profiles: list[SeedModerator], db: AsyncDBSession) -> ModeratorSeedReport:
    """Creates the moderators that do not exist yet, an existing profile is never changed."""
    report = ModeratorSeedReport(created=[], skipped=[])

    for profile in profiles:
        # Cheap check first, bcrypt is spent only on new profiles
        if await Queries.Moderator.get_by_email(profile.email, db) is not None:
            report.skipped.append(profile.email)
            continue

        # Another run may have created it meanwhile, the unique index skips it then
        created = await db.scalar(
            insert(AfdModerator)
            .values(
                email=profile.email,
                first_name=profile.first_name,
                last_name=profile.last_name,
                password_hash=hash_password(profile.password),
            )
            .on_conflict_do_nothing(index_elements=[text("lower(email)")])
            .returning(AfdModerator.id)
        )
        (report.created if created is not None else report.skipped).append(profile.email)

    await db.commit()
    return report
