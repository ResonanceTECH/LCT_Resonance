"""Parameterised question templates (Backend.md, "Механика тестирования").

A generator turns a seed into a concrete question and computes the correct answer in code;
nothing reusable is stored in the bank. Two candidates get different tasks of the same
difficulty, so a leaked instance does not help the next one. Every generator is checked
in tests against an independent computation (SQLite for SQL, the interpreter for Python,
Node for JavaScript when available).
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from textwrap import indent

OPTION_IDS = ("a", "b", "c", "d")


@dataclass(frozen=True)
class QuestionInstance:
    prompt: str
    code: str | None
    options: list[dict[str, str]]  # already shuffled, ids a..d
    correct_option_id: str  # never leaves the backend

    @property
    def correct_text(self) -> str:
        return next(o["text"] for o in self.options if o["id"] == self.correct_option_id)


@dataclass(frozen=True)
class Generator:
    key: str
    specialization: str
    topic: str
    build: Callable[[random.Random], QuestionInstance]


GENERATORS: dict[str, Generator] = {}


def _register(key: str, specialization: str, topic: str):
    def decorator(build: Callable[[random.Random], QuestionInstance]):
        GENERATORS[key] = Generator(key, specialization, topic, build)
        return build

    return decorator


def generate(key: str, seed: int) -> QuestionInstance:
    """Deterministic: the same key and seed always give the same question."""
    return GENERATORS[key].build(random.Random(seed))


def generators_for(specialization: str) -> dict[str, list[Generator]]:
    """Generators of a specialization grouped by topic."""
    by_topic: dict[str, list[Generator]] = {}
    for gen in GENERATORS.values():
        if gen.specialization == specialization:
            by_topic.setdefault(gen.topic, []).append(gen)
    return by_topic


def _multiple_choice(
    rng: random.Random,
    prompt: str,
    code: str | None,
    correct: object,
    distractors: Iterable[object],
) -> QuestionInstance:
    correct_text = str(correct)
    pool: list[str] = []
    for value in distractors:
        text = str(value)
        if text != correct_text and text not in pool:
            pool.append(text)
    if len(pool) < 3:
        raise ValueError(f"generator produced only {len(pool)} distinct distractors")
    values = [correct_text, *rng.sample(pool, 3)]
    rng.shuffle(values)
    options = [{"id": oid, "text": text} for oid, text in zip(OPTION_IDS, values, strict=True)]
    return QuestionInstance(prompt, code, options, OPTION_IDS[values.index(correct_text)])


def _near(value: int, *deltas: int) -> list[int]:
    """Plausible numeric distractors around the answer, never negative."""
    return [value + d for d in deltas if value + d >= 0]


# --- Backend -----------------------------------------------------------------------------


@_register("sql_join_count", "backend", "databases")
def _sql_join_count(rng: random.Random) -> QuestionInstance:
    n_users = rng.randint(4, 7)
    n_orders = rng.randint(5, 10)
    buyers = rng.sample(range(1, n_users + 1), rng.randint(2, n_users - 1))
    order_user_ids = [rng.choice(buyers) for _ in range(n_orders)]
    join = rng.choice(["INNER", "LEFT"])
    without_orders = n_users - len(set(order_user_ids))
    answer = n_orders + (without_orders if join == "LEFT" else 0)
    return _multiple_choice(
        rng,
        f"В users {n_users} строк (id от 1 до {n_users}). В orders {n_orders} строк, "
        f"их user_id: {', '.join(map(str, order_user_ids))}. Сколько строк вернёт запрос?",
        f"SELECT *\nFROM users u\n{join} JOIN orders o ON o.user_id = u.id;",
        answer,
        [
            n_orders,
            n_users,
            n_orders + without_orders,
            n_orders + n_users,
            *_near(answer, 1, -1, 2),
        ],
    )


@_register("sql_group_having", "backend", "databases")
def _sql_group_having(rng: random.Random) -> QuestionInstance:
    user_ids = [rng.randint(1, 5) for _ in range(rng.randint(8, 12))]
    threshold = rng.randint(2, 3)
    counts = Counter(user_ids)
    answer = sum(1 for c in counts.values() if c >= threshold)
    return _multiple_choice(
        rng,
        f"В orders {len(user_ids)} строк, их user_id: {', '.join(map(str, user_ids))}. "
        "Сколько строк вернёт запрос?",
        f"SELECT user_id, COUNT(*)\nFROM orders\nGROUP BY user_id\nHAVING COUNT(*) >= {threshold};",
        answer,
        [
            len(counts),
            len(user_ids),
            sum(1 for c in counts.values() if c > threshold),
            *_near(answer, 1, -1, 2, 3),
        ],
    )


@_register("python_slice", "backend", "python")
def _python_slice(rng: random.Random) -> QuestionInstance:
    a = rng.sample(range(1, 30), rng.randint(6, 8))
    start = rng.randint(0, 2)
    stop = rng.randint(start + 3, len(a))
    step = rng.choice([1, 2])
    expr = f"a[{start}:{stop}:{step}]" if step != 1 else f"a[{start}:{stop}]"
    answer = a[start:stop:step]
    return _multiple_choice(
        rng,
        "Что выведет код?",
        f"a = {a}\nprint({expr})",
        answer,
        [
            a[start : stop + 1 : step],
            a[start + 1 : stop + 1 : step],
            a[start : stop - 1 : step],
            a[start:stop],
            a[start + 1 : stop : step],
            answer[::-1],
        ],
    )


@_register("python_loop_sum", "backend", "python")
def _python_loop_sum(rng: random.Random) -> QuestionInstance:
    start, stop = rng.randint(0, 3), rng.randint(10, 20)
    step, k = rng.choice([1, 2, 3]), rng.choice([2, 3, 4])
    answer = sum(i for i in range(start, stop, step) if i % k == 0)
    return _multiple_choice(
        rng,
        "Что выведет код?",
        f"total = 0\nfor i in range({start}, {stop}, {step}):\n"
        f"    if i % {k} == 0:\n        total += i\nprint(total)",
        answer,
        [
            sum(i for i in range(start, stop + 1, step) if i % k == 0),
            sum(range(start, stop, step)),
            sum(i for i in range(start, stop, step) if i % k != 0),
            *_near(answer, k, -k, step + k),
        ],
    )


@_register("python_dict_last_write", "backend", "python")
def _python_dict_last_write(rng: random.Random) -> QuestionInstance:
    m = rng.choice([3, 4, 5])
    xs = rng.sample(range(1, 40), rng.randint(6, 8))  # more values than remainders
    remainders = Counter(x % m for x in xs)
    # Ask about a colliding key: that is where "the last write wins" matters.
    key = rng.choice(sorted(r for r, n in remainders.items() if n > 1))
    group = [x for x in xs if x % m == key]
    answer = group[-1]
    return _multiple_choice(
        rng,
        "Что выведет код?",
        f"xs = {xs}\nd = {{x % {m}: x for x in xs}}\nprint(d[{key}])",
        answer,
        [group[0], sum(group), max(group), xs[-1], key, *_near(answer, m, -m, 1, -1)],
    )


_COMPLEXITIES = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(n³)"]
_LOOP_PATTERNS = [
    ("for i in range(n):\n    total += {c}", "O(n)"),
    ("for i in range(n):\n    for j in range({c}):\n        total += j", "O(n)"),
    ("for i in range(n):\n    for j in range(n):\n        total += i * j", "O(n²)"),
    ("for i in range(n):\n    for j in range(i):\n        total += 1", "O(n²)"),
    ("i = n\nwhile i > 1:\n    i //= {k}\n    total += 1", "O(log n)"),
    (
        "for i in range(n):\n    j = n\n    while j > 1:\n        j //= {k}\n        total += 1",
        "O(n log n)",
    ),
    (
        "for i in range(n):\n    for j in range(n):\n"
        "        for m in range(n):\n            total += 1",
        "O(n³)",
    ),
    ("total = n * {c} + {k}", "O(1)"),
]


@_register("big_o_complexity", "backend", "algorithms")
def _big_o_complexity(rng: random.Random) -> QuestionInstance:
    body, answer = rng.choice(_LOOP_PATTERNS)
    body = body.format(c=rng.randint(2, 100), k=rng.choice([2, 3]))
    code = f"def f(n):\n    total = 0\n{indent(body, '    ')}\n    return total"
    return _multiple_choice(
        rng, "Какова асимптотическая сложность функции f по n?", code, answer, _COMPLEXITIES
    )


# --- Frontend ----------------------------------------------------------------------------

_JS_STATEMENTS = {
    "sync": "console.log({n});",
    "timeout": "setTimeout(() => console.log({n}));",
    "promise": "Promise.resolve().then(() => console.log({n}));",
    "microtask": "queueMicrotask(() => console.log({n}));",
}


@_register("js_event_loop_order", "frontend", "javascript")
def _js_event_loop_order(rng: random.Random) -> QuestionInstance:
    kinds = ["sync", "timeout", rng.choice(["promise", "microtask"])]
    kinds += rng.choices(list(_JS_STATEMENTS), k=rng.randint(1, 2))
    rng.shuffle(kinds)
    numbered = list(enumerate(kinds, start=1))
    code = "\n".join(_JS_STATEMENTS[kind].format(n=n) for n, kind in numbered)

    def order(*groups: tuple[str, ...]) -> str:
        return " ".join(str(n) for group in groups for n, kind in numbered if kind in group)

    # Synchronous code first, then the microtask queue, then timers (macrotasks).
    answer = order(("sync",), ("promise", "microtask"), ("timeout",))
    return _multiple_choice(
        rng,
        "В каком порядке выведутся числа?",
        code,
        answer,
        [
            " ".join(str(n) for n, _ in numbered),
            order(("sync",), ("timeout",), ("promise", "microtask")),
            order(("promise", "microtask"), ("sync",), ("timeout",)),
            order(("timeout",), ("promise", "microtask"), ("sync",)),
            " ".join(answer.split()[::-1]),
        ],
    )


@_register("js_array_chain", "frontend", "javascript")
def _js_array_chain(rng: random.Random) -> QuestionInstance:
    arr = rng.sample(range(1, 20), 6)
    # The threshold is one of the values, so `>` and `>=` give different answers.
    k, m = rng.choice(sorted(arr)[1:-1]), rng.choice([2, 3])
    answer = sum(x * m for x in arr if x > k)
    return _multiple_choice(
        rng,
        "Что выведет код?",
        f"const arr = {arr};\n"
        f"console.log(arr.filter(x => x > {k}).map(x => x * {m}).reduce((s, x) => s + x, 0));",
        answer,
        [
            sum(x * m for x in arr if x >= k),
            sum(x for x in arr if x > k),
            sum(x * m for x in arr),
            sum(x * m for x in arr if x < k),
            *_near(answer, m, -m),
        ],
    )


@_register("js_coercion", "frontend", "javascript")
def _js_coercion(rng: random.Random) -> QuestionInstance:
    a, b = rng.sample(range(2, 10), 2)
    op = rng.choice(["+", "-", "*"])
    results = {"+": f"{a}{b}", "-": str(a - b), "*": str(a * b)}
    numeric = {"+": a + b, "-": f"{a}{b}", "*": f"{a}{b}"}
    return _multiple_choice(
        rng,
        "Что выведет код?",
        f'console.log("{a}" {op} {b});',
        results[op],
        [numeric[op], "NaN", "TypeError", f"{b}{a}"],
    )


@_register("react_state_batching", "frontend", "react")
def _react_state_batching(rng: random.Random) -> QuestionInstance:
    initial = rng.randint(0, 5)
    updates = [("fn", rng.randint(1, 3)), ("value", rng.randint(1, 5))]
    updates += [(rng.choice(["fn", "value"]), rng.randint(1, 3))]
    rng.shuffle(updates)
    lines, state = [], initial
    for kind, delta in updates:
        if kind == "fn":
            lines.append(f"  setCount(c => c + {delta});")
            state += delta
        else:
            # `count` is the value captured at render time, not the queued state.
            lines.append(f"  setCount(count + {delta});")
            state = initial + delta
    naive = initial + sum(delta for _, delta in updates)
    return _multiple_choice(
        rng,
        "Чему будет равен count после одного клика? Обработчик вызывается один раз.",
        f"const [count, setCount] = useState({initial});\n\n"
        "function handleClick() {\n" + "\n".join(lines) + "\n}",
        state,
        [naive, initial + updates[-1][1], initial, *_near(state, 1, -1, 2)],
    )
