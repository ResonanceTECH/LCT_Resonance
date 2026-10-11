import uuid

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.candidate import CandidateUpdate
from app.schemas.offer import OfferCreate
from app.schemas.vacancy import VacancyUpdate


def _offer(**overrides) -> dict:
    payload = {
        "candidateId": str(uuid.uuid4()),
        "positionTitle": "Backend",
        "message": "Join us",
        "salaryFrom": 200000,
        "salaryTo": 250000,
    }
    payload.update(overrides)
    return payload


def _error_types(exc: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    return {e["type"] for e in exc.value.errors()}


def test_api_accepts_and_returns_camel_case():
    offer = OfferCreate(**_offer(vacancyId=""))
    assert offer.vacancy_id is None  # an unselected <select> sends ""
    assert "positionTitle" in offer.model_dump(by_alias=True)


def test_salary_range_must_not_be_inverted():
    with pytest.raises(ValidationError) as exc:
        OfferCreate(**_offer(salaryFrom=300000, salaryTo=100000))
    assert "invalid_salary_range" in _error_types(exc)


def test_only_rubles_are_accepted():
    with pytest.raises(ValidationError) as exc:
        OfferCreate(**_offer(currency="USD"))
    assert "currency_not_supported" in _error_types(exc)


def test_profile_form_blanks_and_zero_salary_mean_not_set():
    update = CandidateUpdate(about="  ", city="", salaryFrom=0, salaryTo=300000)
    assert (update.about, update.city, update.salary_from) == (None, None, None)


def test_profile_rejects_unknown_enum_values_and_nulls():
    with pytest.raises(ValidationError):
        CandidateUpdate(workFormat="anywhere")
    with pytest.raises(ValidationError):
        CandidateUpdate(readiness=None)
    with pytest.raises(ValidationError):
        VacancyUpdate(title=None)


def test_registration_needs_display_name_and_strong_enough_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="a@example.com",
            password="1234567",
            role="candidate",
            displayName="Аня",
            termsAccepted=True,
            personalDataConsent=True,
        )
    ok = RegisterRequest(
        email="a@example.com",
        password="12345678",
        role="employer",
        displayName="Аня",
        termsAccepted=True,
        personalDataConsent=True,
    )
    assert ok.display_name == "Аня"
    assert ok.public_passport_consent is False


def test_registration_requires_separate_terms_and_personal_data_consents():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="a@example.com",
            password="12345678",
            role="candidate",
            displayName="Аня",
            termsAccepted=False,
            personalDataConsent=True,
        )
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="a@example.com",
            password="12345678",
            role="candidate",
            displayName="Аня",
            termsAccepted=True,
            personalDataConsent=False,
        )


def test_login_accepts_any_stored_address():
    # Registration validates the format; login must not reject existing accounts.
    login = LoginRequest(email="admin@example.invalid", password="x")
    assert login.email == "admin@example.invalid"
