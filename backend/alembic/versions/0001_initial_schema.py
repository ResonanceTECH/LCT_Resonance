"""Initial schema: every table of the MVP in one migration.

The project has no production data yet, so the schema is created from scratch rather
than replayed through incremental changes. Demo data: `python -m app.seed`.

Revision ID: 0001
Revises:
Create Date: 2026-10-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Creation order; dropped in reverse so foreign keys never point at a missing table.
TABLES = [
    "grades",
    "skills",
    "specializations",
    "users",
    "audit_events",
    "auth_sessions",
    "candidate_profiles",
    "companies",
    "consents",
    "email_verification_tokens",
    "notifications",
    "test_questions",
    "candidate_skills",
    "fsp_achievements",
    "fsp_links",
    "profile_views",
    "shortlist_items",
    "test_attempts",
    "vacancies",
    "applications",
    "offers",
    "saved_vacancies",
    "test_attempt_items",
    "vacancy_skills",
]


def _timestamp(name: str) -> sa.Column:
    """NOT NULL timestamp filled by the database (created_at, updated_at, ...)."""
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "grades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "specializations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ux_users_email", "users", [sa.literal_column("lower(email)")], unique=True)
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_auth_sessions_refresh_token_hash", "auth_sessions", ["refresh_token_hash"], unique=True
    )
    op.create_table(
        "candidate_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("telegram", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("experience_description", sa.Text(), nullable=True),
        sa.Column("desired_position", sa.String(length=255), nullable=True),
        sa.Column("declared_specialization_id", sa.UUID(), nullable=True),
        sa.Column("declared_grade_id", sa.UUID(), nullable=True),
        sa.Column("verified_specialization_id", sa.UUID(), nullable=True),
        sa.Column("verified_grade_id", sa.UUID(), nullable=True),
        sa.Column("grade_verification_status", sa.String(length=32), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("work_format", sa.String(length=32), nullable=True),
        sa.Column("readiness", sa.String(length=32), nullable=False),
        sa.Column("profile_visibility", sa.String(length=32), nullable=False),
        sa.Column("contacts_visibility", sa.String(length=32), nullable=False),
        sa.Column("last_grade_change_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_score", sa.Integer(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.CheckConstraint("currency = 'RUB'", name="ck_candidate_currency"),
        sa.CheckConstraint(
            "readiness IN ('actively_looking', 'open_to_offers', 'not_looking')",
            name="ck_candidate_readiness",
        ),
        sa.CheckConstraint(
            "salary_from IS NULL OR salary_from > 0", name="ck_candidate_salary_from"
        ),
        sa.CheckConstraint(
            "salary_to IS NULL OR salary_from IS NULL OR salary_to >= salary_from",
            name="ck_candidate_salary_range",
        ),
        sa.ForeignKeyConstraint(
            ["declared_grade_id"],
            ["grades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["declared_specialization_id"],
            ["specializations.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["verified_grade_id"],
            ["grades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["verified_specialization_id"],
            ["specializations.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_candidate_category",
        "candidate_profiles",
        ["verified_specialization_id", "verified_grade_id", "readiness"],
        unique=False,
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("contact_name", sa.String(length=128), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_companies_owner_user_id", "companies", ["owner_user_id"], unique=True)
    op.create_table(
        "consents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consents_user_type", "consents", ["user_id", "type"], unique=False)
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_email_verification_tokens_token_hash",
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("href", sa.String(length=512), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "test_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("specialization_id", sa.UUID(), nullable=False),
        sa.Column("grade_id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_answer", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("exposure_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["grades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["specialization_id"],
            ["specializations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_user_id", "skill_id", name="uq_candidate_skill"),
    )
    op.create_index(
        "ix_candidate_skills_skill",
        "candidate_skills",
        ["skill_id", "candidate_user_id"],
        unique=False,
    )
    op.create_table(
        "fsp_achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("achievement_type", sa.String(length=64), nullable=False),
        sa.Column("discipline", sa.String(length=255), nullable=True),
        sa.Column("competition_name", sa.String(length=255), nullable=True),
        sa.Column("result", sa.String(length=255), nullable=True),
        sa.Column("place", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("sport_rank", sa.String(length=128), nullable=True),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_user_id", "source", "external_id", name="uq_fsp_achievement"
        ),
    )
    op.create_table(
        "fsp_links",
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("fsp_member_id", sa.String(length=128), nullable=False),
        sa.Column("sync_status", sa.String(length=32), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("candidate_user_id"),
        sa.UniqueConstraint("fsp_member_id"),
    )
    op.create_table(
        "profile_views",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("employer_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "viewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["employer_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_views_candidate", "profile_views", ["candidate_user_id"], unique=False
    )
    op.create_table(
        "shortlist_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employer_user_id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["employer_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employer_user_id", "candidate_user_id", name="uq_shortlist_item"),
    )
    op.create_table(
        "test_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("specialization_id", sa.UUID(), nullable=False),
        sa.Column("grade_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stack", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_retest", sa.Boolean(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["grades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["specialization_id"],
            ["specializations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vacancies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("specialization_id", sa.UUID(), nullable=False),
        sa.Column("grade_id", sa.UUID(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("work_format", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("extra_info", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.CheckConstraint("salary_from > 0", name="ck_vacancy_salary_from"),
        sa.CheckConstraint("salary_to >= salary_from", name="ck_vacancy_salary_range"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["grades.id"],
        ),
        sa.ForeignKeyConstraint(
            ["specialization_id"],
            ["specializations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vacancies_search",
        "vacancies",
        ["specialization_id", "grade_id", "status"],
        unique=False,
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("vacancy_id", sa.UUID(), nullable=False),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_application"),
    )
    op.create_table(
        "offers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employer_user_id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("vacancy_id", sa.UUID(), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("position_title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("work_format", sa.String(length=32), nullable=False),
        sa.Column("employer_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("salary_from > 0", name="ck_offer_salary_from"),
        sa.CheckConstraint("salary_to >= salary_from", name="ck_offer_salary_range"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["employer_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vacancy_id"],
            ["vacancies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_offers_candidate_status", "offers", ["candidate_user_id", "status"], unique=False
    )
    op.create_index(
        "ix_offers_employer_status", "offers", ["employer_user_id", "status"], unique=False
    )
    op.create_index(
        "uq_offers_active_no_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('new', 'viewed') AND vacancy_id IS NULL"),
    )
    op.create_index(
        "uq_offers_active_vacancy",
        "offers",
        ["employer_user_id", "candidate_user_id", "vacancy_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('new', 'viewed') AND vacancy_id IS NOT NULL"),
    )
    op.create_table(
        "saved_vacancies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("candidate_user_id", sa.UUID(), nullable=False),
        sa.Column("vacancy_id", sa.UUID(), nullable=False),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["candidate_user_id"], ["candidate_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_user_id", "vacancy_id", name="uq_saved_vacancy"),
    )
    op.create_table(
        "test_attempt_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=True),
        sa.Column("generator_key", sa.String(length=64), nullable=True),
        sa.Column("seed", sa.BigInteger(), nullable=True),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_option_id", sa.String(length=32), nullable=False),
        sa.Column("selected_option_id", sa.String(length=32), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["test_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["test_questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "position", name="uq_attempt_item_position"),
    )
    op.create_table(
        "vacancy_skills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vacancy_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vacancy_id", "skill_id", name="uq_vacancy_skill"),
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table)
