
from typing import Annotated
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select
 
DATABASE_URL = "sqlite:///./portfolio.db"
connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
 
 
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    name: str
    firstname: str
    phone: str
    github: str | None = None
    bio: str | None = None
 
 
class Skill(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    level: str | None = None  # ex: "Débutant", "Intermédiaire", "Expert"
 
 
class Education(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    degree: str        # Intitulé du diplôme
    school: str        # Établissement
    start_date: str    # ex: "Sep 2020"
    end_date: str | None = None   # None = en cours
    description: str | None = None
 
 
class Experience(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str          # Intitulé du poste
    company: str        # Entreprise
    start_date: str     # ex: "Jan 2022"
    end_date: str | None = None   # None = poste actuel
    description: str | None = None
 
 
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
 
 
app = FastAPI()
templates = Jinja2Templates(directory="templates")
 
 
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
 
 
# ── Accueil / Création utilisateur ─────────────────────────────────────────
 
@app.get("/")
def show_home(request: Request):
    return templates.TemplateResponse(request, "index.html", context={})
 
 
@app.post("/")
def create_user(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    name: Annotated[str, Form()],
    firstname: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    github: Annotated[str, Form()] = "",
    bio: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        user = User(
            username=username, email=email, name=name,
            firstname=firstname, phone=phone, github=github, bio=bio,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return RedirectResponse(f"/portfolio/{user.id}", status_code=303)
 
 
# ── Portfolio ───────────────────────────────────────────────────────────────
 
@app.get("/portfolio/{user_id}")
def show_portfolio(request: Request, user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        skills = session.exec(select(Skill).where(Skill.user_id == user_id)).all()
        experiences = session.exec(
            select(Experience).where(Experience.user_id == user_id)
        ).all()
        educations = session.exec(
            select(Education).where(Education.user_id == user_id)
        ).all()
        return templates.TemplateResponse(
            request, "portfolio.html",
            context={"user": user, "skills": skills, "experiences": experiences, "educations": educations},
        )
 
 
# ── Skills ──────────────────────────────────────────────────────────────────
 
@app.post("/portfolio/{user_id}/skills/add")
def add_skill(
    user_id: int,
    name: Annotated[str, Form()],
    level: Annotated[str, Form()] = "",
):
    with Session(engine) as session:
        skill = Skill(user_id=user_id, name=name, level=level or None)
        session.add(skill)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
@app.post("/portfolio/{user_id}/skills/{skill_id}/delete")
def delete_skill(user_id: int, skill_id: int):
    with Session(engine) as session:
        skill = session.get(Skill, skill_id)
        if not skill or skill.user_id != user_id:
            raise HTTPException(status_code=404, detail="Compétence introuvable")
        session.delete(skill)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
# ── Expériences ─────────────────────────────────────────────────────────────
 
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
        exp = Experience(
            user_id=user_id, title=title, company=company,
            start_date=start_date,
            end_date=end_date or None,
            description=description or None,
        )
        session.add(exp)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
@app.post("/portfolio/{user_id}/experiences/{exp_id}/delete")
def delete_experience(user_id: int, exp_id: int):
    with Session(engine) as session:
        exp = session.get(Experience, exp_id)
        if not exp or exp.user_id != user_id:
            raise HTTPException(status_code=404, detail="Expérience introuvable")
        session.delete(exp)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
# ── Formations ──────────────────────────────────────────────────────────────
 
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
        edu = Education(
            user_id=user_id, degree=degree, school=school,
            start_date=start_date,
            end_date=end_date or None,
            description=description or None,
        )
        session.add(edu)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
@app.post("/portfolio/{user_id}/educations/{edu_id}/delete")
def delete_education(user_id: int, edu_id: int):
    with Session(engine) as session:
        edu = session.get(Education, edu_id)
        if not edu or edu.user_id != user_id:
            raise HTTPException(status_code=404, detail="Formation introuvable")
        session.delete(edu)
        session.commit()
    return RedirectResponse(f"/portfolio/{user_id}", status_code=303)
 
 
# ── Liste utilisateurs ──────────────────────────────────────────────────────
 
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
        # Supprimer les skills et expériences liés
        for skill in session.exec(select(Skill).where(Skill.user_id == user_id)).all():
            session.delete(skill)
        for exp in session.exec(select(Experience).where(Experience.user_id == user_id)).all():
            session.delete(exp)
        for edu in session.exec(select(Education).where(Education.user_id == user_id)).all():
            session.delete(edu)
        session.delete(user)
        session.commit()
        return RedirectResponse("/users", status_code=303)