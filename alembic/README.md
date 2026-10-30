# How to migrate 101

After making changes in models inside application side, you must create an empty revision and **never autogenerate**

The steps:

1. Create an empty revision

```bash
uv run alembic revision -m "subject: did" --rev-id 000n_subject_revision
```

2. Write upgrades/downgrades by hand in created your *versions/000n_subject_revision*

```py
def upgrade() -> None:
    # op - alembic, sa - sqlalchemy
    # new required column on a table with rows: add nullable, fill, then set NOT NULL
    op.add_column('subject', sa.Column('name_normalized', sa.VARCHAR(255), nullable=True))
    op.execute("UPDATE subject SET name_normalized = lower(name)")
    op.alter_column('subject', 'name_normalized', existing_type=sa.VARCHAR(255), nullable=False)

def downgrade() -> None:
    # reverse to upgrade
    op.drop_column('subject', 'name_normalized') 
```

FUO:
- Columns: op.add_column / op.drop_column / op.alter_column(..., existing_type=..., nullable=...)
- Indecies and constraints: op.create_index / op.create_foreign_key / op.create_unique_constraint
- Raw SQL: op.execute("...")
- For enums use raw: op.execute("ALTER TYPE x ADD VALUE 'y'")

3. Apply and Verify

```bash
uv run alembic upgrade head     # or use Ctrl + Shift + P -> Tasks: Run Task -> Alembic: Upgrade to head
uv run alembic downgrade -1 
uv run alembic upgrade head
uv run alembic check            # Only search about changes you've done, anything else is gibberish
```

# Do not:
- **db_init is now baseline**: do not change directly, use migrations above
- **revisions from main are permanent**: do not change them, or migrations will ruin themselves
- **carefull with merging**: if someone working on revisions concurent with you, make an agreement

# Done!