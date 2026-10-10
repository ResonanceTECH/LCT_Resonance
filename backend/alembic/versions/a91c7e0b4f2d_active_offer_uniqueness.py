"""Add integrity indexes for sessions, company ownership, and active offers.

Revision ID: a91c7e0b4f2d
Revises: e54cfea96046
Create Date: 2026-10-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a91c7e0b4f2d"
down_revision: Union[str, Sequence[str], None] = "e54cfea96046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rows that would violate the new unique indexes. Databases seeded by the old seed script
# have two companies for one employer; fail with a clear hint instead of a raw SQL error.
_DUPLICATE_CHECKS = {
    "companies.owner_user_id": (
        "SELECT owner_user_id FROM companies GROUP BY owner_user_id HAVING count(*) > 1"
    ),
    "active offers": (
        "SELECT 1 FROM offers WHERE status IN ('sent', 'viewed') "
        "GROUP BY employer_user_id, candidate_user_id, vacancy_id HAVING count(*) > 1"
    ),
}


def _assert_no_duplicates() -> None:
    conn = op.get_bind()
    for what, query in _DUPLICATE_CHECKS.items():
        if conn.execute(sa.text(query)).first() is not None:
            raise RuntimeError(
                f"Duplicate {what} block revision {revision}. On a demo database recreate it: "
                "`alembic downgrade base && alembic upgrade head && python -m app.seed`."
            )


def upgrade() -> None:
    _assert_no_duplicates()
    op.create_index(
        "uq_auth_sessions_refresh_token_hash",
        "auth_sessions",
        ["refresh_token_hash"],
        unique=True,
    )
    op.create_index(
        "uq_email_verification_tokens_token_hash",
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "uq_companies_owner_user_id",
        "companies",
        ["owner_user_id"],
        unique=True,
    )
    op.create_index(
        "uq_offers_active_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id", "vacancy_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('sent', 'viewed') AND vacancy_id IS NOT NULL"),
    )
    op.create_index(
        "uq_offers_active_no_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('sent', 'viewed') AND vacancy_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_email_verification_tokens_token_hash", table_name="email_verification_tokens"
    )
    op.drop_index("uq_auth_sessions_refresh_token_hash", table_name="auth_sessions")
    op.drop_index("uq_offers_active_no_vacancy", table_name="offers")
    op.drop_index("uq_offers_active_vacancy", table_name="offers")
    op.drop_index("uq_companies_owner_user_id", table_name="companies")
