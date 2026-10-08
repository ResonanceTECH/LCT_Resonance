"""initial_schema

Revision ID: e54cfea96046
Revises:
Create Date: 2026-10-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e54cfea96046"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ux_users_email", "users", [sa.text("lower(email)")], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "specializations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
    )
    op.create_table(
        "grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "candidate_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("first_name", sa.String(128)),
        sa.Column("last_name", sa.String(128)),
        sa.Column("phone", sa.String(64)),
        sa.Column("telegram", sa.String(128)),
        sa.Column("city", sa.String(128)),
        sa.Column("bio", sa.Text()),
        sa.Column("experience_months", sa.Integer()),
        sa.Column("declared_specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id")),
        sa.Column("declared_grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id")),
        sa.Column("verified_specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id")),
        sa.Column("verified_grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id")),
        sa.Column("grade_verification_status", sa.String(32), nullable=False, server_default="not_tested"),
        sa.Column("salary_min", sa.Integer()),
        sa.Column("work_format", sa.String(32)),
        sa.Column("open_to_offers", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("profile_visibility", sa.String(32), nullable=False, server_default="employers"),
        sa.Column("contacts_visibility", sa.String(32), nullable=False, server_default="after_accept"),
        sa.Column("last_grade_change_at", sa.DateTime(timezone=True)),
        sa.Column("last_test_score", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_candidate_category",
        "candidate_profiles",
        ["verified_specialization_id", "verified_grade_id", "open_to_offers"],
    )

    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="3"),
        sa.UniqueConstraint("candidate_user_id", "skill_id", name="uq_candidate_skill"),
    )
    op.create_index("ix_candidate_skills_skill", "candidate_skills", ["skill_id", "candidate_user_id"])

    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "test_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id"), nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("topic", sa.String(64), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_answer", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "test_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id"), nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("score", sa.Integer()),
        sa.Column("passed", sa.Boolean()),
        sa.Column("status", sa.String(32), nullable=False, server_default="in_progress"),
        sa.Column("question_ids", postgresql.JSONB(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "test_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_questions.id"), nullable=False),
        sa.Column("selected_option_id", sa.String(32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("industry", sa.String(128)),
        sa.Column("website", sa.String(512)),
        sa.Column("contact_name", sa.String(128)),
        sa.Column("contact_email", sa.String(320)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id"), nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("work_format", sa.String(32), nullable=False, server_default="remote"),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="private"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("salary_from > 0", name="ck_vacancy_salary_from"),
        sa.CheckConstraint("salary_to >= salary_from", name="ck_vacancy_salary_range"),
    )
    op.create_index("ix_vacancies_search", "vacancies", ["specialization_id", "grade_id", "status"])

    op.create_table(
        "vacancy_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("vacancy_id", "skill_id", name="uq_vacancy_skill"),
    )

    op.create_table(
        "fsp_links",
        sa.Column("candidate_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("fsp_member_id", sa.String(128), nullable=False, unique=True),
        sa.Column("sync_status", sa.String(32), nullable=False, server_default="none"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("raw_snapshot", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "fsp_achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="fsp"),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("achievement_type", sa.String(64), nullable=False),
        sa.Column("discipline", sa.String(255)),
        sa.Column("competition_name", sa.String(255)),
        sa.Column("result", sa.String(255)),
        sa.Column("place", sa.Integer()),
        sa.Column("role", sa.String(128)),
        sa.Column("sport_rank", sa.String(128)),
        sa.Column("achieved_at", sa.DateTime(timezone=True)),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("candidate_user_id", "source", "external_id", name="uq_fsp_achievement"),
    )

    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("candidate_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vacancies.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("salary_from", sa.Integer(), nullable=False),
        sa.Column("salary_to", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("work_format", sa.String(32), nullable=False, server_default="remote"),
        sa.Column("employer_contact", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True)),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("salary_from > 0", name="ck_offer_salary_from"),
        sa.CheckConstraint("salary_to >= salary_from", name="ck_offer_salary_range"),
    )
    op.create_index("ix_offers_candidate_status", "offers", ["candidate_user_id", "status"])
    op.create_index("ix_offers_employer_status", "offers", ["employer_user_id", "status"])

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_events",
        "offers",
        "fsp_achievements",
        "fsp_links",
        "vacancy_skills",
        "vacancies",
        "companies",
        "test_answers",
        "test_attempts",
        "test_questions",
        "consents",
        "candidate_skills",
        "candidate_profiles",
        "skills",
        "grades",
        "specializations",
        "email_verification_tokens",
        "auth_sessions",
        "users",
    ]:
        op.drop_table(table)
