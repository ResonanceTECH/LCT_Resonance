from app.skills.normalize import canonicalize_skill, normalize_skills


def test_normalize_examples_from_ml_spec():
    assert normalize_skills(["React.js", "TS", "Postgres"]) == [
        "React",
        "TypeScript",
        "PostgreSQL",
    ]


def test_dedupes_variants():
    assert normalize_skills(["React", "ReactJS", "react.js"]) == ["React"]


def test_canonicalize_unknown_keeps_trim():
    assert canonicalize_skill("  ExoticLib  ") == "ExoticLib"
