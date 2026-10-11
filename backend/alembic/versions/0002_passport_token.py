"""Career Passport link token: /p/<name>-<token> instead of the internal user id.

Existing candidates get a token here; new ones get it from the model default.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-11
"""

import secrets
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A copy of app.models.candidate: a migration must not change when the app code does.
ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
LENGTH = 8


def upgrade() -> None:
    op.add_column(
        "candidate_profiles", sa.Column("passport_token", sa.String(length=16), nullable=True)
    )
    bind = op.get_bind()
    user_ids = bind.execute(sa.text("SELECT user_id FROM candidate_profiles")).scalars().all()
    tokens: set[str] = set()
    for user_id in user_ids:
        token = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
        while token in tokens:
            token = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
        tokens.add(token)
        bind.execute(
            sa.text("UPDATE candidate_profiles SET passport_token = :token WHERE user_id = :id"),
            {"token": token, "id": user_id},
        )
    op.alter_column("candidate_profiles", "passport_token", nullable=False)
    op.create_index(
        "uq_candidate_profiles_passport_token",
        "candidate_profiles",
        ["passport_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_candidate_profiles_passport_token", table_name="candidate_profiles")
    op.drop_column("candidate_profiles", "passport_token")
