"""Per-attempt question instances, static exposure counter, consents index.

Generated questions have no row in test_questions, so an attempt now stores the issued
instances (with generator seed) in test_attempt_items. Existing attempts and answers are
copied over before test_answers and test_attempts.question_ids are dropped.

Revision ID: c4e8f1a2b6d3
Revises: a91c7e0b4f2d
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c4e8f1a2b6d3"
down_revision: str | Sequence[str] | None = "a91c7e0b4f2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "test_questions",
        sa.Column("exposure_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "test_attempt_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_questions.id", ondelete="SET NULL"),
        ),
        sa.Column("generator_key", sa.String(64)),
        sa.Column("seed", sa.BigInteger()),
        sa.Column("topic", sa.String(64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("code", sa.Text()),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_option_id", sa.String(32), nullable=False),
        sa.Column("selected_option_id", sa.String(32)),
        sa.Column("is_correct", sa.Boolean()),
        sa.UniqueConstraint("attempt_id", "position", name="uq_attempt_item_position"),
    )
    op.execute(
        """
        INSERT INTO test_attempt_items (
            id, attempt_id, position, source, question_id, topic, prompt, options,
            correct_option_id, selected_option_id, is_correct
        )
        SELECT gen_random_uuid(), a.id, (q.ord - 1)::int, 'static', tq.id, tq.topic,
               tq.prompt, tq.options, tq.correct_answer, ans.selected_option_id, ans.is_correct
        FROM test_attempts a
        CROSS JOIN LATERAL jsonb_array_elements_text(a.question_ids) WITH ORDINALITY AS q(qid, ord)
        JOIN test_questions tq ON tq.id = q.qid::uuid
        LEFT JOIN test_answers ans ON ans.attempt_id = a.id AND ans.question_id = tq.id
        """
    )
    op.drop_table("test_answers")
    op.drop_column("test_attempts", "question_ids")
    op.create_index("ix_consents_user_type", "consents", ["user_id", "type"])


def downgrade() -> None:
    op.drop_index("ix_consents_user_type", table_name="consents")
    op.add_column(
        "test_attempts",
        sa.Column(
            "question_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_table(
        "test_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("test_questions.id"),
            nullable=False,
        ),
        sa.Column("selected_option_id", sa.String(32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
    )
    # Only static items can go back: generated questions never had a test_questions row.
    op.execute(
        """
        UPDATE test_attempts a SET question_ids = COALESCE(
            (SELECT jsonb_agg(i.question_id::text ORDER BY i.position)
             FROM test_attempt_items i
             WHERE i.attempt_id = a.id AND i.question_id IS NOT NULL),
            '[]'::jsonb)
        """
    )
    op.execute(
        """
        INSERT INTO test_answers (id, attempt_id, question_id, selected_option_id, is_correct)
        SELECT gen_random_uuid(), attempt_id, question_id, selected_option_id, is_correct
        FROM test_attempt_items
        WHERE question_id IS NOT NULL AND selected_option_id IS NOT NULL
        """
    )
    op.drop_table("test_attempt_items")
    op.drop_column("test_questions", "exposure_count")
