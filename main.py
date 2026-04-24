from typing import Annotated
from fastapi import FastAPI, Request, Form, HTTPException, status
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


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


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
            username=username,
            email=email,
            name=name,
            firstname=firstname,
            phone=phone,
            github=github,
            bio=bio,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return RedirectResponse(f"/portfolio/{user.id}", status_code=303)


@app.get("/portfolio/{user_id}")
def show_portfolio(request: Request, user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        return templates.TemplateResponse(
            request, "portfolio.html", context={"user": user}
        )


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
        session.delete(user)
        session.commit()
        return RedirectResponse("/users", status_code=303)
