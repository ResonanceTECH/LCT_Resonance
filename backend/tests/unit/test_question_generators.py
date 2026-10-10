"""Generators are checked against independent computations, as Backend.md requires:
a real SQL engine, the Python interpreter and, when installed, Node.js."""

from __future__ import annotations

import contextlib
import io
import re
import shutil
import sqlite3
import subprocess

import pytest

from app.services.question_generators import GENERATORS, OPTION_IDS, generate

SEEDS = range(1000)


@pytest.mark.parametrize("key", sorted(GENERATORS))
def test_generator_shape_and_determinism(key: str):
    for seed in SEEDS:
        q = generate(key, seed)
        texts = [o["text"] for o in q.options]
        assert [o["id"] for o in q.options] == list(OPTION_IDS)
        assert len(set(texts)) == 4, (key, seed, texts)
        assert q.correct_option_id in OPTION_IDS
    assert generate(key, 42) == generate(key, 42)


def test_generators_vary_with_seed():
    for key in GENERATORS:
        variants = {(q.prompt, q.code) for q in (generate(key, seed) for seed in range(30))}
        assert len(variants) > 5, key


def _sqlite_rows(prompt: str, query: str) -> int:
    n_users = re.search(r"В users (\d+) строк", prompt)
    order_ids = [int(x) for x in re.search(r"user_id: ([\d, ]+)\.", prompt).group(1).split(", ")]
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER)")
    if n_users:
        db.executemany(
            "INSERT INTO users VALUES (?)", [(i,) for i in range(1, int(n_users[1]) + 1)]
        )
    db.executemany("INSERT INTO orders (user_id) VALUES (?)", [(u,) for u in order_ids])
    return len(db.execute(query).fetchall())


@pytest.mark.parametrize("key", ["sql_join_count", "sql_group_having"])
def test_sql_answers_match_sqlite(key: str):
    for seed in SEEDS:
        q = generate(key, seed)
        assert q.correct_text == str(_sqlite_rows(q.prompt, q.code)), (seed, q.code)


@pytest.mark.parametrize("key", ["python_slice", "python_loop_sum", "python_dict_last_write"])
def test_python_answers_match_interpreter(key: str):
    for seed in SEEDS:
        q = generate(key, seed)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(q.code, {})  # code built by our generator, not user input
        assert q.correct_text == out.getvalue().strip(), (seed, q.code)


def test_react_batching_matches_queue_semantics():
    for seed in SEEDS:
        q = generate("react_state_batching", seed)
        initial = int(re.search(r"useState\((\d+)\)", q.code)[1])
        state = initial
        for kind, delta in re.findall(r"setCount\((c => c|count) \+ (\d+)\)", q.code):
            state = (state if kind == "c => c" else initial) + int(delta)
        assert q.correct_text == str(state), q.code


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
@pytest.mark.parametrize("key", ["js_event_loop_order", "js_array_chain", "js_coercion"])
def test_js_answers_match_node(key: str):
    for seed in range(25):
        q = generate(key, seed)
        run = subprocess.run(
            ["node", "-e", q.code], capture_output=True, text=True, timeout=10, check=True
        )
        assert q.correct_text == " ".join(run.stdout.split()), (seed, q.code)
