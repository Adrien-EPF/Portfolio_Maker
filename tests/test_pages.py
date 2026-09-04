import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

import main


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(main, "engine", test_engine)
    with TestClient(main.app) as test_client:
        yield test_client


def create_user(client, **overrides):
    data = {
        "username": "jdupont",
        "email": "jdupont@example.com",
        "name": "Dupont",
        "firstname": "Jean",
        "phone": "0600000000",
        "github": "",
        "bio": "",
    }
    data.update(overrides)
    response = client.post("/", data=data, follow_redirects=False)
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    return user_id


def test_home_page_shows_creation_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'name="username"' in response.text


def test_create_user_redirects_and_persists(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}")
    assert response.status_code == 200
    assert "Jean" in response.text
    assert "Dupont" in response.text
    assert "jdupont@example.com" in response.text


def test_portfolio_shows_empty_states_when_no_entries(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}")
    assert response.status_code == 200
    assert "Aucune compétence" in response.text
    assert "Aucune expérience" in response.text
    assert "Aucune formation" in response.text


def test_portfolio_not_found_returns_404(client):
    response = client.get("/portfolio/999")
    assert response.status_code == 404


def test_users_page_shows_empty_state_when_no_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert "Aucun portfolio créé" in response.text


def test_users_page_lists_created_users(client):
    create_user(client, username="jdupont", email="jdupont@example.com")
    response = client.get("/users")
    assert response.status_code == 200
    assert "jdupont" in response.text
    assert "jdupont@example.com" in response.text


def test_add_and_delete_skill(client):
    user_id = create_user(client)

    add_response = client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    portfolio_page = client.get(f"/portfolio/{user_id}")
    assert "Python" in portfolio_page.text
    assert "Expert" in portfolio_page.text

    skill_id = _extract_first_id(portfolio_page.text, "skills")
    delete_response = client.post(
        f"/portfolio/{user_id}/skills/{skill_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    portfolio_page_after = client.get(f"/portfolio/{user_id}")
    assert "Python" not in portfolio_page_after.text


def test_add_and_delete_experience(client):
    user_id = create_user(client)

    add_response = client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={
            "title": "Développeur",
            "company": "Acme",
            "start_date": "2020",
            "end_date": "",
            "description": "",
        },
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    portfolio_page = client.get(f"/portfolio/{user_id}")
    assert "Développeur" in portfolio_page.text
    assert "Acme" in portfolio_page.text

    exp_id = _extract_first_id(portfolio_page.text, "experiences")
    delete_response = client.post(
        f"/portfolio/{user_id}/experiences/{exp_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    portfolio_page_after = client.get(f"/portfolio/{user_id}")
    assert "Acme" not in portfolio_page_after.text


def test_add_and_delete_education(client):
    user_id = create_user(client)

    add_response = client.post(
        f"/portfolio/{user_id}/educations/add",
        data={
            "degree": "Master Informatique",
            "school": "Université de Montpellier",
            "start_date": "2023",
            "end_date": "",
            "description": "",
        },
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    portfolio_page = client.get(f"/portfolio/{user_id}")
    assert "Master Informatique" in portfolio_page.text
    assert "Université de Montpellier" in portfolio_page.text

    edu_id = _extract_first_id(portfolio_page.text, "educations")
    delete_response = client.post(
        f"/portfolio/{user_id}/educations/{edu_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    portfolio_page_after = client.get(f"/portfolio/{user_id}")
    assert "Master Informatique" not in portfolio_page_after.text


def test_delete_user_removes_portfolio(client):
    user_id = create_user(client)
    delete_response = client.post(f"/users/{user_id}/delete", follow_redirects=False)
    assert delete_response.status_code == 303
    assert delete_response.headers["location"] == "/users"

    portfolio_response = client.get(f"/portfolio/{user_id}")
    assert portfolio_response.status_code == 404


def _extract_first_id(html: str, action_segment: str) -> str:
    marker = f"/{action_segment}/"
    start = html.index(marker) + len(marker)
    end = html.index("/", start)
    return html[start:end]
