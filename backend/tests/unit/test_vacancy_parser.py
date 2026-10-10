from app.services.vacancy_parser import _salary, _specialization


def test_salary_ranges_in_thousands_and_full_numbers():
    assert _salary("вилка 300-400 тыс. на руки") == (300000, 400000)
    assert _salary("от 200 000 до 260 000 руб.") == (200000, 260000)
    assert _salary("без зарплаты") == (None, None)


def test_specialization_prefers_title_over_optional_mentions():
    assert _specialization("Senior Python Backend", "FastAPI, PostgreSQL") == "Backend"
    assert _specialization("Frontend-разработчик", "React и TypeScript") == "Frontend"
    assert _specialization("Инженер", "Kubernetes, Terraform") == "DevOps"
    assert _specialization("Менеджер", "общение с клиентами") is None
