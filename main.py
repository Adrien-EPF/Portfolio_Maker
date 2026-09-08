import itertools
import os
from dataclasses import dataclass
from typing import Annotated
from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select

DATABASE_URL = "sqlite:///./portfolio.db"
connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

UPLOAD_DIR = "static/uploads"
ALLOWED_PHOTO_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024

SECTION_TYPES = ["skills", "experience", "education", "photo"]
SECTION_LABELS = {
    "skills": "Compétences",
    "experience": "Expériences",
    "education": "Formation",
    "photo": "Photo",
}


@dataclass
class SkillRow:
    name: str = ""
    level: str = ""


@dataclass
class ExpRow:
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


@dataclass
class EduRow:
    degree: str = ""
    school: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


def _skill_rows(names: list[str], levels: list[str]) -> list[SkillRow]:
    rows = [
        SkillRow(name=n, level=l)
        for n, l in itertools.zip_longest(names, levels, fillvalue="")
    ]
    return rows or [SkillRow()]


def _exp_rows(titles, companies, starts, ends, descriptions) -> list[ExpRow]:
    rows = [
        ExpRow(title=t, company=c, start_date=s, end_date=e, description=d)
        for t, c, s, e, d in itertools.zip_longest(
            titles, companies, starts, ends, descriptions, fillvalue=""
        )
    ]
    return rows or [ExpRow()]


def _edu_rows(degrees, schools, starts, ends, descriptions) -> list[EduRow]:
    rows = [
        EduRow(degree=deg, school=sc, start_date=s, end_date=e, description=d)
        for deg, sc, s, e, d in itertools.zip_longest(
            degrees, schools, starts, ends, descriptions, fillvalue=""
        )
    ]
    return rows or [EduRow()]


def _validate_multi_rows(rows: list[tuple[str, str, str]], detail: str):
    """A row is either fully blank (skipped at save time) or has all three
    required fields — any-but-not-all rejects the whole submission, same
    rule as the original single-row check, applied per row."""
    for a, b, c in rows:
        fields = (a.strip(), b.strip(), c.strip())
        if any(fields) and not all(fields):
            raise HTTPException(status_code=400, detail=detail)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    name: str
    firstname: str
    phone: str
    github: str | None = None
    bio: str | None = None
    photo_filename: str | None = None


class Skill(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    level: str | None = None
    position: int = 0


class Education(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    degree: str
    school: str
    start_date: str
    end_date: str | None = None
    description: str | None = None
    position: int = 0


class Experience(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    company: str
    start_date: str
    end_date: str | None = None
    description: str | None = None
    position: int = 0


class PortfolioSection(SQLModel, table=True):
    """A Section a User has added to their Portfolio. Row presence = active.
    Removing a Section deletes only this row — the underlying Skill/Experience/
    Education rows (or the uploaded photo) are never touched, so re-adding the
    Section restores exactly what was there. See docs/adr/0002."""
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    section_type: str
    position: int = 0


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def _table_has_column(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _add_column_if_missing(conn, table: str, column: str, column_def: str):
    if not _table_has_column(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))


def migrate_schema():
    """Brings a pre-existing portfolio.db (created before Sections existed) up
    to date. create_all() only creates missing tables, so tables that already
    exist need their new columns added explicitly."""
    with engine.connect() as conn:
        for table in ("skill", "experience", "education"):
            _add_column_if_missing(conn, table, "position", "position INTEGER DEFAULT 0")
        _add_column_if_missing(conn, "user", "photo_filename", "photo_filename VARCHAR")
        conn.commit()


def backfill_sections():
    """Existing Users already have Skill/Experience/Education rows from before
    Sections were opt-in. Mark those Sections active so nothing they already
    entered appears to vanish."""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            active_types = {
                s.section_type
                for s in session.exec(
                    select(PortfolioSection).where(PortfolioSection.user_id == user.id)
                ).all()
            }
            position = len(active_types)
            for section_type, model in (
                ("skills", Skill),
                ("experience", Experience),
                ("education", Education),
            ):
                if section_type in active_types:
                    continue
                has_data = session.exec(
                    select(model).where(model.user_id == user.id)
                ).first()
                if has_data:
                    session.add(
                        PortfolioSection(
                            user_id=user.id, section_type=section_type, position=position
                        )
                    )
                    position += 1
        session.commit()


def get_active_sections(session: Session, user_id: int) -> list[PortfolioSection]:
    return session.exec(
        select(PortfolioSection)
        .where(PortfolioSection.user_id == user_id)
        .order_by(PortfolioSection.position)
    ).all()


def ensure_section_active(session: Session, user_id: int, section_type: str) -> PortfolioSection:
    existing = session.exec(
        select(PortfolioSection).where(
            PortfolioSection.user_id == user_id,
            PortfolioSection.section_type == section_type,
        )
    ).first()
    if existing:
        return existing
    sections = get_active_sections(session, user_id)
    next_pos = (max((s.position for s in sections), default=-1)) + 1
    section = PortfolioSection(user_id=user_id, section_type=section_type, position=next_pos)
    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def next_position(session: Session, model, user_id: int) -> int:
    rows = session.exec(select(model).where(model.user_id == user_id)).all()
    return max((row.position for row in rows), default=-1) + 1


def move_item(session: Session, model, user_id: int, item_id: int, direction: str):
    items = session.exec(
        select(model).where(model.user_id == user_id).order_by(model.position)
    ).all()
    idx = next((i for i, item in enumerate(items) if item.id == item_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Élément introuvable")
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(items):
        items[idx].position, items[swap_idx].position = items[swap_idx].position, items[idx].position
        session.add(items[idx])
        session.add(items[swap_idx])
        session.commit()


def move_section(session: Session, user_id: int, section_type: str, direction: str):
    sections = get_active_sections(session, user_id)
    idx = next((i for i, s in enumerate(sections) if s.section_type == section_type), None)
    if idx is None:
        return
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(sections):
        sections[idx].position, sections[swap_idx].position = (
            sections[swap_idx].position,
            sections[idx].position,
        )
        session.add(sections[idx])
        session.add(sections[swap_idx])
        session.commit()


async def _read_and_validate_photo(photo: UploadFile) -> tuple[bytes, str]:
    filename = photo.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Format de photo non supporté (jpg, png, webp uniquement)"
        )
    contents = await photo.read()
    if len(contents) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=400, detail="Photo trop volumineuse (5 Mo maximum)")
    return contents, ext


def _write_photo_file(user_id: int, ext: str, contents: bytes) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"user_{user_id}.{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(contents)
    return filename


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    migrate_schema()
    backfill_sections()


# Accueil

@app.get("/")
def show_home(request: Request):
    return templates.TemplateResponse(request, "index.html", context={})


# Création utilisateur

@app.get("/create")
def show_create_form(request: Request):
    return templates.TemplateResponse(
        request, "create.html",
        context={
            "username": "", "email": "", "name": "", "firstname": "", "phone": "",
            "github": "", "bio": "",
            "activate_skills": False, "activate_experience": False,
            "activate_education": False, "activate_photo": False,
            "skill_rows": [SkillRow()], "exp_rows": [ExpRow()], "edu_rows": [EduRow()],
        },
    )


@app.post("/create")
async def create_user(
    request: Request,
    username: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    firstname: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    github: Annotated[str, Form()] = "",
    bio: Annotated[str, Form()] = "",
    activate_skills: Annotated[str | None, Form()] = None,
    skill_name: Annotated[list[str], Form()] = [],
    skill_level: Annotated[list[str], Form()] = [],
    activate_experience: Annotated[str | None, Form()] = None,
    exp_title: Annotated[list[str], Form()] = [],
    exp_company: Annotated[list[str], Form()] = [],
    exp_start_date: Annotated[list[str], Form()] = [],
    exp_end_date: Annotated[list[str], Form()] = [],
    exp_description: Annotated[list[str], Form()] = [],
    activate_education: Annotated[str | None, Form()] = None,
    edu_degree: Annotated[list[str], Form()] = [],
    edu_school: Annotated[list[str], Form()] = [],
    edu_start_date: Annotated[list[str], Form()] = [],
    edu_end_date: Annotated[list[str], Form()] = [],
    edu_description: Annotated[list[str], Form()] = [],
    activate_photo: Annotated[str | None, Form()] = None,
    photo: Annotated[UploadFile | None, File()] = None,
    add_row: Annotated[str | None, Form()] = None,
):
    skill_rows = _skill_rows(skill_name, skill_level)
    exp_rows = _exp_rows(exp_title, exp_company, exp_start_date, exp_end_date, exp_description)
    edu_rows = _edu_rows(edu_degree, edu_school, edu_start_date, edu_end_date, edu_description)

    if add_row:
        if add_row == "skills":
            skill_rows.append(SkillRow())
        elif add_row == "experience":
            exp_rows.append(ExpRow())
        elif add_row == "education":
            edu_rows.append(EduRow())
        else:
            raise HTTPException(status_code=400, detail="Section inconnue")
        return templates.TemplateResponse(
            request, "create.html",
            context={
                "username": username, "email": email, "name": name, "firstname": firstname,
                "phone": phone, "github": github, "bio": bio,
                "activate_skills": bool(activate_skills), "activate_experience": bool(activate_experience),
                "activate_education": bool(activate_education), "activate_photo": bool(activate_photo),
                "skill_rows": skill_rows, "exp_rows": exp_rows, "edu_rows": edu_rows,
            },
        )

    if not all(v.strip() for v in (username, email, name, firstname, phone)):
        raise HTTPException(status_code=422, detail="Identité et contact requis")

    _validate_multi_rows(
        [(r.title, r.company, r.start_date) for r in exp_rows],
        "Expérience incomplète : intitulé, entreprise et date de début sont requis ensemble",
    )
    _validate_multi_rows(
        [(r.degree, r.school, r.start_date) for r in edu_rows],
        "Formation incomplète : diplôme, établissement et date de début sont requis ensemble",
    )

    photo_contents, photo_ext = None, None
    if activate_photo and photo is not None and photo.filename:
        photo_contents, photo_ext = await _read_and_validate_photo(photo)

    with Session(engine) as session:
        user = User(
            username=username, email=email, name=name,
            firstname=firstname, phone=phone, github=github, bio=bio,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        if activate_skills:
            ensure_section_active(session, user.id, "skills")
            position = 0
            for row in skill_rows:
                if row.name.strip():
                    session.add(
                        Skill(user_id=user.id, name=row.name, level=row.level or None, position=position)
                    )
                    position += 1

        if activate_experience:
            ensure_section_active(session, user.id, "experience")
            position = 0
            for row in exp_rows:
                if row.title.strip() and row.company.strip() and row.start_date.strip():
                    session.add(
                        Experience(
                            user_id=user.id, title=row.title, company=row.company,
                            start_date=row.start_date, end_date=row.end_date or None,
                            description=row.description or None, position=position,
                        )
                    )
                    position += 1

        if activate_education:
            ensure_section_active(session, user.id, "education")
            position = 0
            for row in edu_rows:
                if row.degree.strip() and row.school.strip() and row.start_date.strip():
                    session.add(
                        Education(
                            user_id=user.id, degree=row.degree, school=row.school,
                            start_date=row.start_date, end_date=row.end_date or None,
                            description=row.description or None, position=position,
                        )
                    )
                    position += 1

        if activate_photo:
            ensure_section_active(session, user.id, "photo")
            if photo_contents is not None:
                user.photo_filename = _write_photo_file(user.id, photo_ext, photo_contents)
                session.add(user)

        session.commit()
        return RedirectResponse(f"/portfolio/{user.id}", status_code=303)


# Portfolio (vue publique, lecture seule — le CV)

@app.get("/portfolio/{user_id}")
def show_portfolio(request: Request, user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        active_sections = get_active_sections(session, user_id)
        active_types = {s.section_type for s in active_sections}
        skills = session.exec(
            select(Skill).where(Skill.user_id == user_id).order_by(Skill.position)
        ).all() if "skills" in active_types else []
        experiences = session.exec(
            select(Experience).where(Experience.user_id == user_id).order_by(Experience.position)
        ).all() if "experience" in active_types else []
        educations = session.exec(
            select(Education).where(Education.user_id == user_id).order_by(Education.position)
        ).all() if "education" in active_types else []
        return templates.TemplateResponse(
            request, "portfolio.html",
            context={
                "user": user, "skills": skills, "experiences": experiences, "educations": educations,
                "active_types": active_types,
            },
        )


# Portfolio (gestion — modification de tout le contenu)

@app.get("/portfolio/{user_id}/edit")
def show_portfolio_edit(
    request: Request,
    user_id: int,
    edit: str | None = None,
    edit_skill: int | None = None,
    edit_experience: int | None = None,
    edit_education: int | None = None,
):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        skills = session.exec(
            select(Skill).where(Skill.user_id == user_id).order_by(Skill.position)
        ).all()
        experiences = session.exec(
            select(Experience).where(Experience.user_id == user_id).order_by(Experience.position)
        ).all()
        educations = session.exec(
            select(Education).where(Education.user_id == user_id).order_by(Education.position)
        ).all()
        active_sections = get_active_sections(session, user_id)
        active_types = {s.section_type for s in active_sections}
        inactive_types = [t for t in SECTION_TYPES if t not in active_types]
        return templates.TemplateResponse(
            request, "portfolio_edit.html",
            context={
                "user": user, "skills": skills, "experiences": experiences, "educations": educations,
                "active_sections": active_sections, "active_types": active_types,
                "inactive_types": inactive_types, "section_labels": SECTION_LABELS,
                "editing_profile": edit == "profile",
                "editing_skill_id": edit_skill,
                "editing_experience_id": edit_experience,
                "editing_education_id": edit_education,
            },
        )


@app.post("/portfolio/{user_id}/edit")
def edit_user(
    user_id: int,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    name: Annotated[str, Form()],
    firstname: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    github: Annotated[str, Form()] = "",
    bio: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        user.username = username
        user.email = email
        user.name = name
        user.firstname = firstname
        user.phone = phone
        user.github = github
        user.bio = bio
        session.add(user)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Sections

@app.post("/portfolio/{user_id}/sections/{section_type}/add")
def add_section(user_id: int, section_type: str):
    if section_type not in SECTION_TYPES:
        raise HTTPException(status_code=404, detail="Section inconnue")
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        ensure_section_active(session, user_id, section_type)
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/sections/{section_type}/remove")
def remove_section(user_id: int, section_type: str):
    with Session(engine) as session:
        section = session.exec(
            select(PortfolioSection).where(
                PortfolioSection.user_id == user_id,
                PortfolioSection.section_type == section_type,
            )
        ).first()
        if section:
            session.delete(section)
            session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/sections/{section_type}/move")
def move_section_route(user_id: int, section_type: str, direction: Annotated[str, Form()]):
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Direction invalide")
    with Session(engine) as session:
        move_section(session, user_id, section_type, direction)
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Skills

@app.post("/portfolio/{user_id}/skills/add")
def add_skill(
    user_id: int,
    name: Annotated[str, Form()],
    level: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        ensure_section_active(session, user_id, "skills")
        position = next_position(session, Skill, user_id)
        skill = Skill(user_id=user_id, name=name, level=level or None, position=position)
        session.add(skill)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/skills/{skill_id}/edit")
def edit_skill(
    user_id: int,
    skill_id: int,
    name: Annotated[str, Form()],
    level: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        skill = session.get(Skill, skill_id)
        if not skill or skill.user_id != user_id:
            raise HTTPException(status_code=404, detail="Compétence introuvable")
        skill.name = name
        skill.level = level or None
        session.add(skill)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/skills/{skill_id}/delete")
def delete_skill(user_id: int, skill_id: int):
    with Session(engine) as session:
        skill = session.get(Skill, skill_id)
        if not skill or skill.user_id != user_id:
            raise HTTPException(status_code=404, detail="Compétence introuvable")
        session.delete(skill)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/skills/{skill_id}/move")
def move_skill(user_id: int, skill_id: int, direction: Annotated[str, Form()]):
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Direction invalide")
    with Session(engine) as session:
        move_item(session, Skill, user_id, skill_id, direction)
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Expériences

@app.post("/portfolio/{user_id}/experiences/add")
def add_experience(
    user_id: int,
    title: Annotated[str, Form()],
    company: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        ensure_section_active(session, user_id, "experience")
        position = next_position(session, Experience, user_id)
        exp = Experience(
            user_id=user_id, title=title, company=company,
            start_date=start_date,
            end_date=end_date or None,
            description=description or None,
            position=position,
        )
        session.add(exp)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/experiences/{exp_id}/edit")
def edit_experience(
    user_id: int,
    exp_id: int,
    title: Annotated[str, Form()],
    company: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        exp = session.get(Experience, exp_id)
        if not exp or exp.user_id != user_id:
            raise HTTPException(status_code=404, detail="Expérience introuvable")
        exp.title = title
        exp.company = company
        exp.start_date = start_date
        exp.end_date = end_date or None
        exp.description = description or None
        session.add(exp)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/experiences/{exp_id}/delete")
def delete_experience(user_id: int, exp_id: int):
    with Session(engine) as session:
        exp = session.get(Experience, exp_id)
        if not exp or exp.user_id != user_id:
            raise HTTPException(status_code=404, detail="Expérience introuvable")
        session.delete(exp)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/experiences/{exp_id}/move")
def move_experience(user_id: int, exp_id: int, direction: Annotated[str, Form()]):
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Direction invalide")
    with Session(engine) as session:
        move_item(session, Experience, user_id, exp_id, direction)
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Formations

@app.post("/portfolio/{user_id}/educations/add")
def add_education(
    user_id: int,
    degree: Annotated[str, Form()],
    school: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        ensure_section_active(session, user_id, "education")
        position = next_position(session, Education, user_id)
        edu = Education(
            user_id=user_id, degree=degree, school=school,
            start_date=start_date,
            end_date=end_date or None,
            description=description or None,
            position=position,
        )
        session.add(edu)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/educations/{edu_id}/edit")
def edit_education(
    user_id: int,
    edu_id: int,
    degree: Annotated[str, Form()],
    school: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        edu = session.get(Education, edu_id)
        if not edu or edu.user_id != user_id:
            raise HTTPException(status_code=404, detail="Formation introuvable")
        edu.degree = degree
        edu.school = school
        edu.start_date = start_date
        edu.end_date = end_date or None
        edu.description = description or None
        session.add(edu)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/educations/{edu_id}/delete")
def delete_education(user_id: int, edu_id: int):
    with Session(engine) as session:
        edu = session.get(Education, edu_id)
        if not edu or edu.user_id != user_id:
            raise HTTPException(status_code=404, detail="Formation introuvable")
        session.delete(edu)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


@app.post("/portfolio/{user_id}/educations/{edu_id}/move")
def move_education(user_id: int, edu_id: int, direction: Annotated[str, Form()]):
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Direction invalide")
    with Session(engine) as session:
        move_item(session, Education, user_id, edu_id, direction)
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Photo

@app.post("/portfolio/{user_id}/photo/upload")
async def upload_photo(user_id: int, photo: Annotated[UploadFile, File()]):
    contents, ext = await _read_and_validate_photo(photo)

    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        if user.photo_filename:
            old_path = os.path.join(UPLOAD_DIR, user.photo_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

        user.photo_filename = _write_photo_file(user_id, ext, contents)
        session.add(user)
        ensure_section_active(session, user_id, "photo")
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}/edit", status_code=303)


# Liste utilisateurs

@app.get("/users")
def list_users(request: Request):
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return templates.TemplateResponse(
            request, "users.html", context={"users": users}
        )


@app.post("/users/{user_id}/delete")
def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        for skill in session.exec(select(Skill).where(Skill.user_id == user_id)).all():
            session.delete(skill)
        for exp in session.exec(select(Experience).where(Experience.user_id == user_id)).all():
            session.delete(exp)
        for edu in session.exec(select(Education).where(Education.user_id == user_id)).all():
            session.delete(edu)
        for section in session.exec(
            select(PortfolioSection).where(PortfolioSection.user_id == user_id)
        ).all():
            session.delete(section)
        if user.photo_filename:
            photo_path = os.path.join(UPLOAD_DIR, user.photo_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        session.delete(user)
        session.commit()
        return RedirectResponse("/users", status_code=303)
