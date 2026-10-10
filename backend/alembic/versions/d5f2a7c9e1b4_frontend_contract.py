"""Align the schema with the frontend contract (frontend/src/entities/types.ts).

- users.display_name; candidate profile fields of CandidateProfile (fullName, about,
  experienceYears, desiredPosition, salaryFrom/To, currency, readiness);
- vacancy companyName/city/extraInfo, statuses draft|active|closed|archived;
- offer companyName/positionTitle/message, statuses new|viewed|accepted|declined;
- test sessions answered one by one (current_index, stack, is_retest), status completed;
- shortlist, applications, saved vacancies, profile views, notifications.

Existing rows are converted in place.

Revision ID: d5f2a7c9e1b4
Revises: c4e8f1a2b6d3
Create Date: 2026-10-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d5f2a7c9e1b4"
down_revision: str | Sequence[str] | None = "c4e8f1a2b6d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)

_CANDIDATE_CHECKS = {
    "ck_candidate_readiness": "readiness IN ('actively_looking', 'open_to_offers', 'not_looking')",
    "ck_candidate_currency": "currency = 'RUB'",
    "ck_candidate_salary_from": "salary_from IS NULL OR salary_from > 0",
    "ck_candidate_salary_range": (
        "salary_to IS NULL OR salary_from IS NULL OR salary_to >= salary_from"
    ),
}


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _fk(name: str, target: str) -> sa.Column:
    return sa.Column(name, UUID, sa.ForeignKey(target, ondelete="CASCADE"), nullable=False)


def _active_offer_indexes(active: str) -> None:
    op.create_index(
        "uq_offers_active_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id", "vacancy_id"],
        unique=True,
        postgresql_where=sa.text(f"status IN ('{active}', 'viewed') AND vacancy_id IS NOT NULL"),
    )
    op.create_index(
        "uq_offers_active_no_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id"],
        unique=True,
        postgresql_where=sa.text(f"status IN ('{active}', 'viewed') AND vacancy_id IS NULL"),
    )


def _drop_active_offer_indexes() -> None:
    op.drop_index("uq_offers_active_no_vacancy", table_name="offers")
    op.drop_index("uq_offers_active_vacancy", table_name="offers")


def upgrade() -> None:
    # --- users / candidate profiles ------------------------------------------------------
    op.add_column(
        "users", sa.Column("display_name", sa.String(255), nullable=False, server_default="")
    )
    op.alter_column("candidate_profiles", "bio", new_column_name="about")
    op.alter_column("candidate_profiles", "salary_min", new_column_name="salary_from")
    for column in (
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("experience_years", sa.Integer()),
        sa.Column("experience_description", sa.Text()),
        sa.Column("desired_position", sa.String(255)),
        sa.Column("salary_to", sa.Integer()),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("readiness", sa.String(32), nullable=False, server_default="open_to_offers"),
    ):
        op.add_column("candidate_profiles", column)
    op.execute(
        """
        UPDATE candidate_profiles SET
            full_name = trim(concat_ws(' ', first_name, last_name)),
            experience_years = experience_months / 12,
            readiness = CASE WHEN open_to_offers THEN 'open_to_offers' ELSE 'not_looking' END,
            salary_from = NULLIF(GREATEST(salary_from, 0), 0)
        """
    )
    op.execute(
        """
        UPDATE users u SET display_name = cp.full_name
        FROM candidate_profiles cp WHERE cp.user_id = u.id AND cp.full_name <> ''
        """
    )
    op.execute("UPDATE users SET display_name = split_part(email, '@', 1) WHERE display_name = ''")
    op.drop_index("ix_candidate_category", table_name="candidate_profiles")
    for column in ("first_name", "last_name", "experience_months", "open_to_offers"):
        op.drop_column("candidate_profiles", column)
    op.create_index(
        "ix_candidate_category",
        "candidate_profiles",
        ["verified_specialization_id", "verified_grade_id", "readiness"],
    )
    for name, condition in _CANDIDATE_CHECKS.items():
        op.create_check_constraint(name, "candidate_profiles", condition)

    # --- vacancies -------------------------------------------------------------------------
    op.add_column(
        "vacancies", sa.Column("company_name", sa.String(255), nullable=False, server_default="")
    )
    op.add_column("vacancies", sa.Column("city", sa.String(128)))
    op.add_column("vacancies", sa.Column("extra_info", sa.Text()))
    op.execute(
        "UPDATE vacancies v SET company_name = c.name FROM companies c WHERE c.id = v.company_id"
    )
    op.execute("UPDATE vacancies SET status = 'active' WHERE status = 'published'")
    op.drop_column("vacancies", "visibility")

    # --- offers ----------------------------------------------------------------------------
    op.alter_column("offers", "title", new_column_name="position_title")
    op.alter_column("offers", "description", new_column_name="message")
    op.add_column(
        "offers", sa.Column("company_name", sa.String(255), nullable=False, server_default="")
    )
    op.execute(
        "UPDATE offers o SET company_name = c.name FROM companies c WHERE c.id = o.company_id"
    )
    _drop_active_offer_indexes()
    op.execute("UPDATE offers SET status = 'new' WHERE status = 'sent'")
    op.execute("UPDATE offers SET status = 'declined' WHERE status = 'rejected'")
    op.alter_column("offers", "status", server_default="new")
    _active_offer_indexes("new")

    # --- test sessions -----------------------------------------------------------------------
    op.add_column(
        "test_attempts",
        sa.Column(
            "stack", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    op.add_column(
        "test_attempts",
        sa.Column("is_retest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "test_attempts",
        sa.Column("current_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE test_attempts SET status = 'completed' WHERE status = 'submitted'")
    op.execute(
        """
        UPDATE test_attempts a SET current_index = (
            SELECT count(*) FROM test_attempt_items i
            WHERE i.attempt_id = a.id AND i.selected_option_id IS NOT NULL)
        """
    )

    # --- engagement ----------------------------------------------------------------------------
    op.create_table(
        "shortlist_items",
        sa.Column("id", UUID, primary_key=True),
        _fk("employer_user_id", "users.id"),
        _fk("candidate_user_id", "candidate_profiles.user_id"),
        _created_at(),
        sa.UniqueConstraint("employer_user_id", "candidate_user_id", name="uq_shortlist_item"),
    )
    op.create_table(
        "applications",
        sa.Column("id", UUID, primary_key=True),
        _fk("candidate_user_id", "candidate_profiles.user_id"),
        _fk("vacancy_id", "vacancies.id"),
        _created_at(),
        sa.UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_application"),
    )
    op.create_table(
        "saved_vacancies",
        sa.Column("id", UUID, primary_key=True),
        _fk("candidate_user_id", "candidate_profiles.user_id"),
        _fk("vacancy_id", "vacancies.id"),
        _created_at(),
        sa.UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_saved_vacancy"),
    )
    op.create_table(
        "profile_views",
        sa.Column("id", UUID, primary_key=True),
        _fk("candidate_user_id", "candidate_profiles.user_id"),
        _fk("employer_user_id", "users.id"),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_profile_views_candidate", "profile_views", ["candidate_user_id"])
    op.create_table(
        "notifications",
        sa.Column("id", UUID, primary_key=True),
        _fk("user_id", "users.id"),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("href", sa.String(512)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        _created_at(),
    )
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_profile_views_candidate", table_name="profile_views")
    for table in (
        "notifications",
        "profile_views",
        "saved_vacancies",
        "applications",
        "shortlist_items",
    ):
        op.drop_table(table)

    op.execute("UPDATE test_attempts SET status = 'submitted' WHERE status = 'completed'")
    for column in ("current_index", "is_retest", "stack"):
        op.drop_column("test_attempts", column)

    _drop_active_offer_indexes()
    op.execute("UPDATE offers SET status = 'sent' WHERE status = 'new'")
    op.execute("UPDATE offers SET status = 'rejected' WHERE status = 'declined'")
    op.alter_column("offers", "status", server_default="sent")
    _active_offer_indexes("sent")
    op.drop_column("offers", "company_name")
    op.alter_column("offers", "message", new_column_name="description")
    op.alter_column("offers", "position_title", new_column_name="title")

    op.add_column(
        "vacancies",
        sa.Column("visibility", sa.String(32), nullable=False, server_default="public"),
    )
    op.execute("UPDATE vacancies SET status = 'published' WHERE status = 'active'")
    op.execute("UPDATE vacancies SET status = 'closed' WHERE status = 'archived'")
    for column in ("extra_info", "city", "company_name"):
        op.drop_column("vacancies", column)

    for name in _CANDIDATE_CHECKS:
        op.drop_constraint(name, "candidate_profiles", type_="check")
    op.drop_index("ix_candidate_category", table_name="candidate_profiles")
    op.add_column("candidate_profiles", sa.Column("first_name", sa.String(128)))
    op.add_column("candidate_profiles", sa.Column("last_name", sa.String(128)))
    op.add_column("candidate_profiles", sa.Column("experience_months", sa.Integer()))
    op.add_column(
        "candidate_profiles",
        sa.Column("open_to_offers", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.execute(
        """
        UPDATE candidate_profiles SET
            first_name = NULLIF(split_part(full_name, ' ', 1), ''),
            last_name = NULLIF(
                trim(substr(full_name, length(split_part(full_name, ' ', 1)) + 1)), ''),
            experience_months = experience_years * 12,
            open_to_offers = readiness <> 'not_looking'
        """
    )
    for column in (
        "readiness",
        "currency",
        "salary_to",
        "desired_position",
        "experience_description",
        "experience_years",
        "full_name",
    ):
        op.drop_column("candidate_profiles", column)
    op.alter_column("candidate_profiles", "salary_from", new_column_name="salary_min")
    op.alter_column("candidate_profiles", "about", new_column_name="bio")
    op.create_index(
        "ix_candidate_category",
        "candidate_profiles",
        ["verified_specialization_id", "verified_grade_id", "open_to_offers"],
    )
    op.drop_column("users", "display_name")
