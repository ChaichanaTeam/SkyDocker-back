from datetime import date

from pydantic import BaseModel, Field

from backend_src.models import FlyingPrivileges


class VerificationApproval(BaseModel):
    privilege_expiry: dict[FlyingPrivileges, date] = Field(
        default_factory=dict,
        description="Last valid day of every privilege in the request, read by the moderator from the certificate",
    )
