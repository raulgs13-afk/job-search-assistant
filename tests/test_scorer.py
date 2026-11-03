import pytest

from jobassistant.scoring.scorer import parse_score
from types import SimpleNamespace

from jobassistant.scoring.scorer import extract_text
from jobassistant.scoring.scorer import is_obviously_senior
from jobassistant.scoring.scorer import required_years, skip_reason


def test_required_years_detection():
    assert required_years("Requisitos: 5+ años de experiencia en Python") == 5
    assert required_years("3 years of experience with APIs") == 3
    assert required_years("Experiencia previa de 2 años") == 2
    assert required_years("No se requiere experiencia") is None


def test_skip_reason():
    assert skip_reason("Senior Developer", "") == "título senior"
    assert "4 años" in skip_reason("Developer", "Al menos 4 años de experiencia")
    assert skip_reason("Junior Developer", "Se valoran 1 año de experiencia") is None

def test_senior_titles_are_skipped():
    assert is_obviously_senior("Senior Site Reliability Engineer")
    assert is_obviously_senior("Director Of Engineering")


def test_junior_titles_are_kept():
    assert not is_obviously_senior("Junior Python Developer")
    assert not is_obviously_senior("Senior Mentor for Junior Developers")
    assert not is_obviously_senior("AI Engineer")

def test_parse_valid_json():
    text = '{"best_profile": "software_ia", "score": 85, "reasons": ["Python"], "missing_skills": ["AWS"]}'
    assert parse_score(text).score == 85


def test_extract_text_ignores_thinking_blocks():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking="..."),
            SimpleNamespace(type="text", text='{"a": 1}'),
        ]
    )
    assert extract_text(response) == '{"a": 1}'


def test_parse_json_with_markdown_fences():
    text = '```json\n{"best_profile": "none", "score": 10, "reasons": [], "missing_skills": []}\n```'
    assert parse_score(text).best_profile == "none"


def test_parse_rejects_out_of_range_score():
    text = '{"best_profile": "software_ia", "score": 150, "reasons": [], "missing_skills": []}'
    with pytest.raises(ValueError):
        parse_score(text)