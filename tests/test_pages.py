import re

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
    monkeypatch.setattr(main, "UPLOAD_DIR", str(tmp_path / "uploads"))
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


def test_portfolio_starts_with_no_active_sections(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}")
    assert response.status_code == 200
    assert "Ajouter la section Compétences" in response.text
    assert "Ajouter la section Expériences" in response.text
    assert "Ajouter la section Formation" in response.text
    assert "Ajouter la section Photo" in response.text
    assert "Aucune compétence" not in response.text


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


def test_adding_skill_activates_its_section(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}")
    assert "Retirer la section Compétences" in page.text
    assert "Ajouter la section Compétences" not in page.text


def test_retiring_section_preserves_data_and_readding_restores_it(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )

    remove_response = client.post(
        f"/portfolio/{user_id}/sections/skills/remove", follow_redirects=False
    )
    assert remove_response.status_code == 303
    page_after_remove = client.get(f"/portfolio/{user_id}")
    assert "Python" not in page_after_remove.text
    assert "Ajouter la section Compétences" in page_after_remove.text

    add_back_response = client.post(
        f"/portfolio/{user_id}/sections/skills/add", follow_redirects=False
    )
    assert add_back_response.status_code == 303
    page_after_readd = client.get(f"/portfolio/{user_id}")
    assert "Python" in page_after_readd.text


def test_move_section_changes_display_order(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Dev", "company": "Acme", "start_date": "2020"},
        follow_redirects=False,
    )

    page_before = client.get(f"/portfolio/{user_id}").text
    assert page_before.index(">Compétences<") < page_before.index(">Expériences<")

    move_response = client.post(
        f"/portfolio/{user_id}/sections/experience/move",
        data={"direction": "up"},
        follow_redirects=False,
    )
    assert move_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}").text
    assert page_after.index(">Expériences<") < page_after.index(">Compétences<")


def test_move_item_changes_order_within_section(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Rust"}, follow_redirects=False
    )
    page_before = client.get(f"/portfolio/{user_id}")
    assert page_before.text.index("Python") < page_before.text.index("Rust")

    python_id = _extract_first_id(page_before.text, "skills")
    move_response = client.post(
        f"/portfolio/{user_id}/skills/{python_id}/move",
        data={"direction": "down"},
        follow_redirects=False,
    )
    assert move_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}")
    assert page_after.text.index("Rust") < page_after.text.index("Python")


def test_photo_upload_activates_section_and_shows_image(client):
    user_id = create_user(client)
    upload_response = client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")},
        follow_redirects=False,
    )
    assert upload_response.status_code == 303
    page = client.get(f"/portfolio/{user_id}")
    assert f"/static/uploads/user_{user_id}.png" in page.text
    assert "Retirer la section Photo" in page.text


def test_photo_upload_rejects_unsupported_extension(client):
    user_id = create_user(client)
    response = client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 400


def _extract_first_id(html: str, action_segment: str) -> str:
    match = re.search(rf"/{action_segment}/(\d+)/", html)
    return match.group(1)
