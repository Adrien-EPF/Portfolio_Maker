from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

user_list = []

templates = Jinja2Templates(directory="templates")


class user(BaseModel):
    username: str
    email: str
    password: str


class formation(BaseModel):
    name: str
    start_year: int
    end_year: int


class personalInfo(BaseModel):
    name: str
    firstname: str
    birthday: int
    gender: str
    phone_number: int
    email: str


class project(BaseModel):
    name: str
    start_year: int
    end_year: int
    description: str
    link: str


class experience(BaseModel):
    name: str
    entreprise: str
    description: str
    start_year: int
    end_year: int


@app.get("/")
def display_home_page(request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/")
def add_user(user: user):
    user_list.append(user)
    response = {"user_id": len(user_list) - 1, "info": user}
    return response


@app.get("/users")
def get_users():
    return user_list


@app.get("/admin")
def display_admin_page():
    return "Admin page"
