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
    response = client.post("/create", data=data, follow_redirects=False)
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    return user_id


def test_home_page_shows_two_choices(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/create"' in response.text
    assert 'href="/users"' in response.text
    assert 'name="username"' not in response.text


def test_nav_chrome_is_consistent_across_pages(client):
    user_id = create_user(client)
    for path in ["/", "/create", "/users", f"/portfolio/{user_id}", f"/portfolio/{user_id}/edit"]:
        response = client.get(path)
        assert response.status_code == 200
        text = response.text
        assert '<nav class="site-nav">' in text
        assert 'aria-label="Portfolio Maker, accueil"' in text
        assert 'class="logo-mark"' in text
        assert 'href="/"' in text
        assert 'href="/create"' in text
        assert 'href="/users"' in text
        assert '<footer class="site-footer">' in text
        assert "Portfolio Maker — Projet FastAPI" in text


def test_favicon_and_logo_assets_are_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert '<link rel="icon" type="image/svg+xml" href="/static/favicon.svg" />' in response.text

    assert client.get("/static/logo-pm.svg").status_code == 200
    assert client.get("/static/favicon.svg").status_code == 200


def test_nav_marks_current_page_with_aria_current(client):
    for path, label in [("/", "Accueil"), ("/create", "Créer"), ("/users", "Tous les portfolios")]:
        text = client.get(path).text
        assert f'aria-current="page">{label}</a>' in text


def test_home_page_shows_accueil_copy(client):
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert "Au sommaire" in text
    assert "Un CV en ligne, généré depuis un formulaire." in text
    assert (
        "Pas de compte, pas de mot de passe. Vos informations, les sections dont "
        "vous avez besoin, une page publique — modifiable à tout moment." in text
    )
    assert '<a class="entry-link" href="/create">Créer un portfolio</a>' in text
    assert (
        "Nom, contact, bio — puis les sections Compétences, Formation, "
        "Expérience et Photo, ajoutées à la demande." in text
    )
    assert '<a class="entry-link" href="/users">Voir les portfolios</a>' in text
    assert (
        "La liste des portfolios déjà créés : consultez-en un, ou revenez "
        "modifier le vôtre." in text
    )
    assert '<a href="/create" class="btn btn-primary">Créer un portfolio</a>' in text
    assert '<a href="/users" class="btn btn-ghost">Voir les portfolios</a>' in text


def test_home_page_decorative_elements_are_aria_hidden(client):
    response = client.get("/")
    assert response.text.count('<span class="leader" aria-hidden="true">') == 2
    assert response.text.count('<span class="entry-arrow" aria-hidden="true">') == 2


def test_base_page_loads_instrument_fonts_and_broadsheet_stylesheet(client):
    response = client.get("/")
    text = response.text
    assert "Instrument+Sans" in text
    assert "Instrument+Serif" in text
    assert "family=Inter" not in text
    assert '<link rel="stylesheet" href="/static/style.css" />' in text
    style_index = text.index('href="/static/style.css"')
    broadsheet_index = text.index('href="/static/broadsheet.css"')
    assert style_index < broadsheet_index


def test_create_page_shows_creation_form(client):
    response = client.get("/create")
    assert response.status_code == 200
    assert 'name="username"' in response.text


def test_create_link_reachable_from_users_page(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert 'href="/create"' in response.text


def test_create_and_users_pages_use_broadsheet_markup_not_legacy_cards(client):
    for path in ["/create", "/users"]:
        text = client.get(path).text
        assert 'class="card"' not in text
        assert "directory-grid" not in text
        assert "directory-card" not in text


def test_create_user_redirects_and_persists(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}")
    assert response.status_code == 200
    assert "Jean" in response.text
    assert "Dupont" in response.text
    assert "jdupont@example.com" in response.text


def test_portfolio_not_found_returns_404(client):
    response = client.get("/portfolio/999")
    assert response.status_code == 404


def test_portfolio_edit_not_found_returns_404(client):
    response = client.get("/portfolio/999/edit")
    assert response.status_code == 404


def test_users_page_shows_empty_state_when_no_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert "Aucun portfolio pour l'instant" in response.text


def test_users_page_lists_created_users(client):
    create_user(client, username="jdupont", email="jdupont@example.com")
    response = client.get("/users")
    assert response.status_code == 200
    assert "jdupont" in response.text
    assert "jdupont@example.com" in response.text


def test_users_page_voir_link_points_to_public_portfolio_not_edit(client):
    user_id = create_user(client)
    response = client.get("/users")
    assert f'href="/portfolio/{user_id}"' in response.text
    assert f'href="/portfolio/{user_id}/edit"' not in response.text


# Public portfolio (the CV)


def test_public_portfolio_starts_with_no_active_sections(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}")
    assert response.status_code == 200
    text = response.text
    assert "Jean" in text
    assert "Dupont" in text
    assert "Ajouter la section" not in text


def test_public_portfolio_shows_active_sections_content(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Développeuse", "company": "Acme", "start_date": "2020"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/educations/add",
        data={"degree": "Master Informatique", "school": "Université de Montpellier", "start_date": "2023"},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}")
    assert page.status_code == 200
    assert "Python" in page.text
    assert "Développeuse" in page.text and "Acme" in page.text
    assert "Master Informatique" in page.text and "Université de Montpellier" in page.text


def test_public_portfolio_omits_section_data_when_section_removed(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/sections/skills/remove", follow_redirects=False
    )
    page = client.get(f"/portfolio/{user_id}")
    assert "Python" not in page.text


def test_public_portfolio_never_shows_management_controls(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False
    )
    page = client.get(f"/portfolio/{user_id}")
    text = page.text
    assert "Ajouter la section" not in text
    assert "Retirer la section" not in text
    assert "Supprimer" not in text
    assert "Modifier mon profil" not in text
    assert "Ajouter une compétence" not in text
    assert "/skills/add" not in text


def test_public_portfolio_omits_optional_fields_when_absent(client):
    user_id = create_user(client)
    page = client.get(f"/portfolio/{user_id}")
    text = page.text
    assert "GitHub" not in text
    assert "<img" not in text


def test_public_portfolio_shows_github_and_photo_when_present(client):
    user_id = create_user(client, github="https://github.com/jdupont")
    client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}")
    text = page.text
    assert "github.com/jdupont" in text
    assert f"/static/uploads/user_{user_id}.png" in text


def test_public_portfolio_skill_level_renders_as_dots_with_aria_label(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}")
    assert 'aria-label="Expert"' in page.text
    assert "●●●" in page.text


def test_pdf_download_returns_pdf_file(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_pdf_download_filename_reflects_user_name(client):
    user_id = create_user(client, firstname="Jean", name="Dupont")
    response = client.get(f"/portfolio/{user_id}/pdf")
    assert 'filename="jean-dupont.pdf"' in response.headers["content-disposition"]


def test_pdf_download_works_with_all_sections_active(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python", "level": "Expert"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Développeuse", "company": "Acme", "start_date": "2020"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/educations/add",
        data={"degree": "Master Informatique", "school": "Université de Montpellier", "start_date": "2023"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")},
        follow_redirects=False,
    )
    response = client.get(f"/portfolio/{user_id}/pdf")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_pdf_download_not_found_returns_404(client):
    response = client.get("/portfolio/999/pdf")
    assert response.status_code == 404


def test_public_portfolio_pdf_link_points_to_download_route_not_print(client):
    user_id = create_user(client)
    page = client.get(f"/portfolio/{user_id}")
    assert f'href="/portfolio/{user_id}/pdf"' in page.text
    assert "window.print()" not in page.text


def test_public_portfolio_has_modifier_link_to_edit_page(client):
    user_id = create_user(client)
    page = client.get(f"/portfolio/{user_id}")
    assert f'href="/portfolio/{user_id}/edit"' in page.text


def test_edit_page_has_link_back_to_public_portfolio(client):
    user_id = create_user(client)
    page = client.get(f"/portfolio/{user_id}/edit")
    assert f'href="/portfolio/{user_id}"' in page.text


# Portfolio management (/portfolio/{id}/edit)


def test_portfolio_edit_starts_with_no_active_sections(client):
    user_id = create_user(client)
    response = client.get(f"/portfolio/{user_id}/edit")
    assert response.status_code == 200
    assert "Ajouter la section Compétences" in response.text
    assert "Ajouter la section Expériences" in response.text
    assert "Ajouter la section Formation" in response.text
    assert "Ajouter la section Photo" in response.text
    assert "Aucune compétence" not in response.text


def test_add_and_delete_skill(client):
    user_id = create_user(client)

    add_response = client.post(
        f"/portfolio/{user_id}/skills/add",
        data={"name": "Python", "level": "Expert"},
        follow_redirects=False,
    )
    assert add_response.status_code == 303
    edit_page = client.get(f"/portfolio/{user_id}/edit")
    assert "Python" in edit_page.text
    assert "Expert" in edit_page.text

    skill_id = _extract_first_id(edit_page.text, "skills")
    delete_response = client.post(
        f"/portfolio/{user_id}/skills/{skill_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    edit_page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "Python" not in edit_page_after.text


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
    edit_page = client.get(f"/portfolio/{user_id}/edit")
    assert "Développeur" in edit_page.text
    assert "Acme" in edit_page.text

    exp_id = _extract_first_id(edit_page.text, "experiences")
    delete_response = client.post(
        f"/portfolio/{user_id}/experiences/{exp_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    edit_page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "Acme" not in edit_page_after.text


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
    edit_page = client.get(f"/portfolio/{user_id}/edit")
    assert "Master Informatique" in edit_page.text
    assert "Université de Montpellier" in edit_page.text

    edu_id = _extract_first_id(edit_page.text, "educations")
    delete_response = client.post(
        f"/portfolio/{user_id}/educations/{edu_id}/delete", follow_redirects=False
    )
    assert delete_response.status_code == 303
    edit_page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "Master Informatique" not in edit_page_after.text


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
    page = client.get(f"/portfolio/{user_id}/edit")
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
    page_after_remove = client.get(f"/portfolio/{user_id}/edit")
    assert "Python" not in page_after_remove.text
    assert "Ajouter la section Compétences" in page_after_remove.text

    add_back_response = client.post(
        f"/portfolio/{user_id}/sections/skills/add", follow_redirects=False
    )
    assert add_back_response.status_code == 303
    page_after_readd = client.get(f"/portfolio/{user_id}/edit")
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

    page_before = client.get(f"/portfolio/{user_id}/edit").text
    assert page_before.index(">Compétences<") < page_before.index(">Expériences<")

    move_response = client.post(
        f"/portfolio/{user_id}/sections/experience/move",
        data={"direction": "up"},
        follow_redirects=False,
    )
    assert move_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}/edit").text
    assert page_after.index(">Expériences<") < page_after.index(">Compétences<")


def test_move_item_changes_order_within_section(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Rust"}, follow_redirects=False
    )
    page_before = client.get(f"/portfolio/{user_id}/edit")
    assert page_before.text.index("Python") < page_before.text.index("Rust")

    python_id = _extract_first_id(page_before.text, "skills")
    move_response = client.post(
        f"/portfolio/{user_id}/skills/{python_id}/move",
        data={"direction": "down"},
        follow_redirects=False,
    )
    assert move_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}/edit")
    assert page_after.text.index("Rust") < page_after.text.index("Python")


def test_photo_upload_activates_section_and_shows_image(client):
    user_id = create_user(client)
    upload_response = client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")},
        follow_redirects=False,
    )
    assert upload_response.status_code == 303
    page = client.get(f"/portfolio/{user_id}/edit")
    assert f"/static/uploads/user_{user_id}.png" in page.text
    assert "Retirer la section Photo" in page.text


def test_photo_upload_rejects_unsupported_extension(client):
    user_id = create_user(client)
    response = client.post(
        f"/portfolio/{user_id}/photo/upload",
        files={"photo": ("avatar.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 400


# Sections chosen and populated at creation time


def test_create_user_with_section_entries_activates_and_populates(client):
    response = client.post(
        "/create",
        data={
            "username": "jdupont",
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
            "activate_skills": "on",
            "skill_name": "Python",
            "skill_level": "Expert",
            "activate_experience": "on",
            "exp_title": "Développeur",
            "exp_company": "Acme",
            "exp_start_date": "2020",
            "activate_education": "on",
            "edu_degree": "Master Informatique",
            "edu_school": "Université de Montpellier",
            "edu_start_date": "2023",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}/edit")
    assert "Retirer la section Compétences" in page.text
    assert "Python" in page.text
    assert "Retirer la section Expériences" in page.text
    assert "Développeur" in page.text and "Acme" in page.text
    assert "Retirer la section Formation" in page.text
    assert "Master Informatique" in page.text


def test_create_user_with_ticked_section_and_blank_entry_activates_with_no_items(client):
    response = client.post(
        "/create",
        data={
            "username": "jdupont",
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
            "activate_skills": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}/edit")
    assert "Retirer la section Compétences" in page.text
    assert "Aucune compétence ajoutée pour le moment." in page.text


def test_create_user_with_partial_experience_fields_is_rejected(client):
    response = client.post(
        "/create",
        data={
            "username": "jdupont",
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
            "activate_experience": "on",
            "exp_title": "Développeur",
        },
    )
    assert response.status_code == 400


def test_create_user_with_partial_education_fields_is_rejected(client):
    response = client.post(
        "/create",
        data={
            "username": "jdupont",
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
            "activate_education": "on",
            "edu_degree": "Master Informatique",
        },
    )
    assert response.status_code == 400


def test_create_user_with_photo_activates_photo_section(client):
    response = client.post(
        "/create",
        data={
            "username": "jdupont",
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
            "activate_photo": "on",
        },
        files={"photo": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}/edit")
    assert f"/static/uploads/user_{user_id}.png" in page.text
    assert "Retirer la section Photo" in page.text


# Multiple Skill/Experience/Education rows at creation time
#
# Repeated form keys are posted as dict values that are lists (e.g.
# skill_name=["Python", "Rust"]) — httpx form-encodes a Mapping's list
# values as repeated keys in order (doseq), which is what FastAPI's
# `list[str] = Form()` parameters expect.


def _base_profile(**overrides):
    data = {
        "username": "jdupont",
        "email": "jdupont@example.com",
        "name": "Dupont",
        "firstname": "Jean",
        "phone": "0600000000",
    }
    data.update(overrides)
    return data


def test_create_user_with_multiple_skill_rows_saves_all(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_skills="on",
            skill_name=["Python", "Rust"],
            skill_level=["Expert", "Débutant"],
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}/edit")
    assert "Python" in page.text
    assert "Rust" in page.text
    assert page.text.index("Python") < page.text.index("Rust")


def test_create_user_with_multiple_experience_rows_saves_all(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_experience="on",
            exp_title=["Développeur", "Consultant"],
            exp_company=["Acme", "Beta"],
            exp_start_date=["2020", "2022"],
            exp_end_date=["", ""],
            exp_description=["", ""],
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}")
    assert "Développeur" in page.text and "Acme" in page.text
    assert "Consultant" in page.text and "Beta" in page.text
    assert page.text.index("Développeur") < page.text.index("Consultant")


def test_create_user_with_multiple_education_rows_saves_all(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_education="on",
            edu_degree=["Licence Informatique", "Master Informatique"],
            edu_school=["Université de Montpellier", "Université de Montpellier"],
            edu_start_date=["2020", "2023"],
            edu_end_date=["2023", ""],
            edu_description=["", ""],
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}")
    assert "Licence Informatique" in page.text
    assert "Master Informatique" in page.text
    assert page.text.index("Licence Informatique") < page.text.index("Master Informatique")


def test_create_user_with_blank_extra_skill_row_is_dropped_silently(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_skills="on",
            skill_name=["Python", ""],
            skill_level=["Expert", ""],
        ),
        follow_redirects=False,
    )
    assert response.status_code == 303
    user_id = int(response.headers["location"].rsplit("/", 1)[-1])
    page = client.get(f"/portfolio/{user_id}/edit")
    assert "Python" in page.text
    assert page.text.count('class="skill-pill"') == 1


def test_create_user_with_partial_second_experience_row_is_rejected(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_experience="on",
            exp_title=["Développeur", "Consultant"],
            exp_company=["Acme", ""],
            exp_start_date=["2020", ""],
            exp_end_date=["", ""],
            exp_description=["", ""],
        ),
    )
    assert response.status_code == 400


def test_create_user_with_partial_second_education_row_is_rejected(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_education="on",
            edu_degree=["Master Informatique", "Licence"],
            edu_school=["Université de Montpellier", ""],
            edu_start_date=["2023", ""],
            edu_end_date=["", ""],
            edu_description=["", ""],
        ),
    )
    assert response.status_code == 400


def test_add_row_reloads_create_page_with_extra_blank_row_and_preserves_typed_values(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_skills="on",
            skill_name=["Python"],
            skill_level=["Expert"],
            add_row="skills",
        ),
    )
    assert response.status_code == 200
    text = response.text
    assert 'value="jdupont"' in text
    assert 'value="Python"' in text
    assert text.count('name="skill_name"') == 2


def test_add_row_for_one_section_leaves_other_sections_row_count_unchanged(client):
    response = client.post(
        "/create",
        data=_base_profile(
            activate_experience="on",
            exp_title=["Développeur"],
            exp_company=["Acme"],
            exp_start_date=["2020"],
            exp_end_date=[""],
            exp_description=[""],
            add_row="skills",
        ),
    )
    assert response.status_code == 200
    text = response.text
    assert text.count('name="skill_name"') == 2
    assert text.count('name="exp_title"') == 1
    assert 'value="Développeur"' in text


# Profile editing


def test_edit_profile_updates_displayed_info(client):
    user_id = create_user(client)
    response = client.post(
        f"/portfolio/{user_id}/edit",
        data={
            "username": "jdupont2",
            "email": "jean.dupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0611111111",
            "github": "https://github.com/jdupont",
            "bio": "Développeur passionné",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get(f"/portfolio/{user_id}/edit")
    assert "jdupont2" in page.text
    assert "jean.dupont@example.com" in page.text
    assert "0611111111" in page.text
    assert "Développeur passionné" in page.text


def test_edit_profile_form_is_prefilled(client):
    user_id = create_user(client)
    page = client.get(f"/portfolio/{user_id}/edit?edit=profile")
    assert page.status_code == 200
    assert 'value="jdupont"' in page.text
    assert 'value="jdupont@example.com"' in page.text


def test_edit_profile_missing_required_field_is_rejected(client):
    user_id = create_user(client)
    response = client.post(
        f"/portfolio/{user_id}/edit",
        data={
            "email": "jdupont@example.com",
            "name": "Dupont",
            "firstname": "Jean",
            "phone": "0600000000",
        },
    )
    assert response.status_code == 422


def test_edit_profile_nonexistent_user_returns_404(client):
    response = client.post(
        "/portfolio/999/edit",
        data={
            "username": "x",
            "email": "x@example.com",
            "name": "X",
            "firstname": "X",
            "phone": "0",
        },
    )
    assert response.status_code == 404


# Editing individual Skill/Experience/Education entries


def test_edit_skill_updates_value_and_keeps_position(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python", "level": "Expert"}, follow_redirects=False
    )
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Rust", "level": "Débutant"}, follow_redirects=False
    )
    page_before = client.get(f"/portfolio/{user_id}/edit")
    python_id = _extract_first_id(page_before.text, "skills")

    edit_response = client.post(
        f"/portfolio/{user_id}/skills/{python_id}/edit",
        data={"name": "Go", "level": "Intermédiaire"},
        follow_redirects=False,
    )
    assert edit_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "<span>Python</span>" not in page_after.text
    assert "<span>Go</span>" in page_after.text
    assert page_after.text.index("Go") < page_after.text.index("Rust")


def test_edit_skill_form_is_prefilled(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/skills/add", data={"name": "Python", "level": "Expert"}, follow_redirects=False
    )
    page = client.get(f"/portfolio/{user_id}/edit")
    skill_id = _extract_first_id(page.text, "skills")

    edit_page = client.get(f"/portfolio/{user_id}/edit?edit_skill={skill_id}")
    assert edit_page.status_code == 200
    assert 'value="Python"' in edit_page.text


def test_edit_skill_wrong_user_returns_404(client):
    user_id = create_user(client)
    other_user_id = create_user(client, username="other", email="other@example.com")
    client.post(f"/portfolio/{user_id}/skills/add", data={"name": "Python"}, follow_redirects=False)
    page = client.get(f"/portfolio/{user_id}/edit")
    skill_id = _extract_first_id(page.text, "skills")

    response = client.post(
        f"/portfolio/{other_user_id}/skills/{skill_id}/edit", data={"name": "Go"}
    )
    assert response.status_code == 404


def test_edit_experience_updates_value_and_keeps_position(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Développeur", "company": "Acme", "start_date": "2020"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Consultant", "company": "Beta", "start_date": "2022"},
        follow_redirects=False,
    )
    page_before = client.get(f"/portfolio/{user_id}/edit")
    first_id = _extract_first_id(page_before.text, "experiences")

    edit_response = client.post(
        f"/portfolio/{user_id}/experiences/{first_id}/edit",
        data={
            "title": "Lead Développeur",
            "company": "Acme",
            "start_date": "2020",
            "end_date": "2021",
            "description": "Encadrement d une equipe technique",
        },
        follow_redirects=False,
    )
    assert edit_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "<h3>Développeur — Acme</h3>" not in page_after.text
    assert "<h3>Lead Développeur — Acme</h3>" in page_after.text
    assert "Encadrement d une equipe technique" in page_after.text
    assert page_after.text.index("Lead Développeur") < page_after.text.index("Consultant")


def test_edit_experience_wrong_user_returns_404(client):
    user_id = create_user(client)
    other_user_id = create_user(client, username="other", email="other@example.com")
    client.post(
        f"/portfolio/{user_id}/experiences/add",
        data={"title": "Développeur", "company": "Acme", "start_date": "2020"},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}/edit")
    exp_id = _extract_first_id(page.text, "experiences")

    response = client.post(
        f"/portfolio/{other_user_id}/experiences/{exp_id}/edit",
        data={"title": "X", "company": "Y", "start_date": "2020"},
    )
    assert response.status_code == 404


def test_edit_education_updates_value_and_keeps_position(client):
    user_id = create_user(client)
    client.post(
        f"/portfolio/{user_id}/educations/add",
        data={"degree": "Master Informatique", "school": "Université de Montpellier", "start_date": "2023"},
        follow_redirects=False,
    )
    client.post(
        f"/portfolio/{user_id}/educations/add",
        data={
            "degree": "Licence Informatique",
            "school": "Université de Montpellier",
            "start_date": "2020",
            "end_date": "2023",
        },
        follow_redirects=False,
    )
    page_before = client.get(f"/portfolio/{user_id}/edit")
    first_id = _extract_first_id(page_before.text, "educations")

    edit_response = client.post(
        f"/portfolio/{user_id}/educations/{first_id}/edit",
        data={
            "degree": "Master Informatique (spécialité IA)",
            "school": "Université de Montpellier",
            "start_date": "2023",
        },
        follow_redirects=False,
    )
    assert edit_response.status_code == 303
    page_after = client.get(f"/portfolio/{user_id}/edit")
    assert "Master Informatique (spécialité IA)" in page_after.text
    assert page_after.text.index("Master Informatique (spécialité IA)") < page_after.text.index(
        "Licence Informatique"
    )


def test_edit_education_wrong_user_returns_404(client):
    user_id = create_user(client)
    other_user_id = create_user(client, username="other", email="other@example.com")
    client.post(
        f"/portfolio/{user_id}/educations/add",
        data={"degree": "Master Informatique", "school": "Université de Montpellier", "start_date": "2023"},
        follow_redirects=False,
    )
    page = client.get(f"/portfolio/{user_id}/edit")
    edu_id = _extract_first_id(page.text, "educations")

    response = client.post(
        f"/portfolio/{other_user_id}/educations/{edu_id}/edit",
        data={"degree": "X", "school": "Y", "start_date": "2020"},
    )
    assert response.status_code == 404


def _extract_first_id(html: str, action_segment: str) -> str:
    match = re.search(rf"/{action_segment}/(\d+)/", html)
    return match.group(1)
