from types import SimpleNamespace

import pytest

from app.models.candidate import PASSPORT_TOKEN_ALPHABET, PASSPORT_TOKEN_LENGTH, new_passport_token
from app.services.passport import NAME_PART_MAX, passport_slug, token_from_slug


def slug(full_name: str, token: str = "k7m2q9xw") -> str:
    return passport_slug(SimpleNamespace(full_name=full_name, passport_token=token))


@pytest.mark.parametrize(
    ("full_name", "expected"),
    [
        ("Анна Ковалёва", "anna-kovaleva-k7m2q9xw"),
        ("Объедков Щукин", "obedkov-shchukin-k7m2q9xw"),
        ("Анна-Мария  Ли", "anna-mariya-li-k7m2q9xw"),
        ("John O'Neil", "john-o-neil-k7m2q9xw"),
        ("", "k7m2q9xw"),
        ("🙂 ???", "k7m2q9xw"),
    ],
)
def test_slug_is_readable_latin(full_name: str, expected: str):
    assert slug(full_name) == expected


def test_long_names_are_cut_on_a_word_boundary():
    name_part = slug("Константин " * 10).removesuffix("-k7m2q9xw")
    assert len(name_part) <= NAME_PART_MAX
    assert set(name_part.split("-")) == {"konstantin"}


@pytest.mark.parametrize(
    ("raw", "token"),
    [
        ("anna-kovaleva-k7m2q9xw", "k7m2q9xw"),
        ("k7m2q9xw", "k7m2q9xw"),
        ("Anna-Kovaleva-K7M2Q9XW", "k7m2q9xw"),
        ("old-name-k7m2q9xw", "k7m2q9xw"),
        ("369b2ac4-c22c-4fcb-8a62-5ea5727cacc5", None),
        ("anna-kovaleva", None),
        ("anna-k7m2q9x1", None),
        ("", None),
    ],
)
def test_only_the_token_identifies_the_passport(raw: str, token: str | None):
    assert token_from_slug(raw) == token


def test_new_tokens_use_the_unambiguous_alphabet():
    tokens = {new_passport_token() for _ in range(500)}
    assert len(tokens) == 500
    for token in tokens:
        assert len(token) == PASSPORT_TOKEN_LENGTH
        assert set(token) <= set(PASSPORT_TOKEN_ALPHABET)
        assert token_from_slug(f"name-{token}") == token
