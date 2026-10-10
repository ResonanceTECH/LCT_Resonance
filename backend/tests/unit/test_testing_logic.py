import random
import uuid
from collections import Counter

from app.models.testing import TestQuestion as QuestionRow  # alias: pytest collects Test*
from app.seed.questions import OPTION_IDS, QUESTION_BANK
from app.services.question_generators import Generator, generators_for
from app.services.testing import BLUEPRINTS, QUESTIONS_PER_TEST, plan_questions, score_percent


def _pool(topics: dict[str, int]) -> list[QuestionRow]:
    return [
        QuestionRow(
            id=uuid.uuid4(), topic=topic, prompt=f"{topic}-{i}", options=[], correct_answer="a"
        )
        for topic, count in topics.items()
        for i in range(count)
    ]


def test_backend_plan_follows_blueprint_and_prefers_generated():
    blueprint = BLUEPRINTS["backend"]
    plan = plan_questions(
        _pool({topic: 6 for topic, _ in blueprint}),
        blueprint,
        generators_for("backend"),
        rng=random.Random(1),
    )
    assert len(plan) == QUESTIONS_PER_TEST
    assert Counter(s.topic for s in plan) == Counter(dict(blueprint))
    # Backend.md: no more than 40% static questions in a backend test.
    assert sum(isinstance(s, Generator) for s in plan) >= 6
    static_ids = [s.id for s in plan if isinstance(s, QuestionRow)]
    assert len(static_ids) == len(set(static_ids))


def test_plan_tops_up_from_other_topics():
    plan = plan_questions(_pool({"http": 1, "misc": 20}), [("http", 3)], {}, rng=random.Random(2))
    assert len(plan) == QUESTIONS_PER_TEST
    assert sum(s.topic == "http" for s in plan) == 1


def test_plan_reuses_generators_when_static_runs_out():
    python = generators_for("backend")["python"]
    plan = plan_questions([], [("python", 5)], {"python": python}, rng=random.Random(3))
    assert len(plan) == QUESTIONS_PER_TEST
    assert all(isinstance(s, Generator) for s in plan)


def test_plan_reports_small_pool():
    assert len(plan_questions(_pool({"misc": 4}), [], {})) == 4


def test_score_percent():
    assert score_percent(7, 10) == 70
    assert score_percent(0, 0) == 0


def test_seed_bank_covers_blueprints():
    for (spec, _grade), questions in QUESTION_BANK.items():
        topics = Counter(q.topic for q in questions)
        for topic, needed in BLUEPRINTS[spec]:
            assert topics[topic] >= needed, (spec, topic)
        assert len(questions) >= QUESTIONS_PER_TEST


def test_seed_answers_are_valid_and_varied():
    for questions in QUESTION_BANK.values():
        assert all(q.correct in OPTION_IDS for q in questions)
        assert len({q.prompt for q in questions}) == len(questions)
        # No single letter may dominate, or "always pick X" would pass the test.
        most_common = Counter(q.correct for q in questions).most_common(1)[0][1]
        assert most_common / len(questions) < 0.5
