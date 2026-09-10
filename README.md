# Portfolio Maker

A small FastAPI app that lets someone fill in a form and get a public, résumé-style page (a "Portfolio") generated from it — no accounts, no login, just a shareable page and a PDF export.

## Features

- Create a User with a bio and contact details (name, email, phone, GitHub)
- Add and reorder Sections: Skills, Experience, Education, Photo — each can be retired and restored without losing data
- Edit everything after creation
- Public Portfolio page per user, downloadable as a PDF
- No authentication: a User is just a database row (see `docs/adr/0001-no-authentication.md`)

## Getting started

### Requirements

- Python 3.10+
- On Windows, PDF export (WeasyPrint) needs the GTK3 runtime installed separately — see WeasyPrint's own installation docs if `/portfolio/{id}/pdf` fails with a missing-library error.

### Install

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Run

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 — the app creates and migrates `portfolio.db` (SQLite) on first startup.

### Test

```bash
pytest
```

## Project structure

```
main.py            FastAPI app: routes, SQLModel models, PDF rendering
templates/          Jinja2 templates (home, create, portfolio, edit, users list)
static/              CSS, logo, favicon, uploaded photos
tests/               pytest suite
docs/adr/            Architecture decision records
CONTEXT.md           Domain vocabulary (User, Portfolio, Section...)
```

## Domain vocabulary

This project uses precise terms for its core concepts — see `CONTEXT.md` for the full glossary (User, Portfolio, Section, Skill, Experience, Education) before naming new code or UI text.
