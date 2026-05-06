# NeuroPulse

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-3.x-B41717?style=flat-square&logo=jinja&logoColor=white)
![Tests](https://img.shields.io/badge/tests-63%20passing-brightgreen?style=flat-square)
![i18n](https://img.shields.io/badge/i18n-EN%20%7C%20ES%20%7C%20FR-blueviolet?style=flat-square)

A decision-neuroscience themed Twitter clone. The feed is filled with fMRI papers, lab struggles, and vmPFC hot takes from 200 simulated researchers.

![NeuroPulse feed](Neuro_Image.png)

---

## Features

| Category | Details |
|---|---|
| **Auth** | Register, login, logout, change password, delete account |
| **Messages** | Post, edit, delete with Markdown + `@mention` + URL auto-link support |
| **Replies** | Reddit-style threaded replies with infinite nesting |
| **Profiles** | Robohash avatars, bio (Markdown), age, per-user message history |
| **Search** | Full-text search across messages and usernames with pagination |
| **i18n** | Language switcher — English, Spanish, French (cookie-persisted) |
| **Security** | Parameterized SQL (injection-proof), Jinja2 auto-escape + markdown safe mode (XSS-proof) |
| **API** | `GET /messages/json` — paginated JSON feed |

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create the database (200 users, 40 000 neuroscience messages)
python db_create.py

# 3. Start the dev server
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000**

> **WSL users:** run both `pip install` and `uvicorn` inside WSL — the Windows and WSL Python environments are separate.

---

## Pre-loaded accounts

| Username | Password | Notes |
|---|---|---|
| `Mike` | `524euTjrWm6uK2C5iw8mC6aNgX1JI78o` | Admin account used in tests |
| `Trump` | `Trump` | Seed user |
| `Biden` | `Biden` | Seed user |
| `Evan` | `correct horse battery staple` | Seed user |
| `Kristen` | `Possible-Rich-Absolute-Battle` | Seed user |

---

## Running the tests

All test files live in `tests/`. Run them from the **project root**:

```bash
python tests/test_all.py         # 19 feature checks
python tests/test_security.py    # 9  security checks (SQL injection, XSS, auth bypass)
python tests/test_integration.py # 35 full-journey checks
```

Or run the full suite at once:

```bash
python tests/test_all.py && python tests/test_security.py && python tests/test_integration.py
```

---

## Project structure

```
NeuroPulse/
├── main.py              # FastAPI app — all routes and business logic
├── db_create.py         # Schema + seed data (200 users, 40 k messages)
├── translations.py      # EN / ES / FR string dictionaries
├── requirements.txt
├── twitter_clone.db     # SQLite database (generated — not committed)
├── Neuro_Image.png      # Screenshot for README
├── static/
│   ├── style.css        # fMRI activation-map colour theme
│   └── neuron.svg       # Axial brain-scan SVG banner
├── templates/
│   ├── base.html        # Layout, nav, language switcher
│   ├── index.html       # Live feed
│   ├── thread.html      # Threaded reply view
│   ├── profile.html     # User profile + message history
│   ├── search.html      # Search results
│   ├── login.html
│   ├── logout.html
│   ├── create_message.html
│   ├── create_user.html
│   ├── edit_message.html
│   ├── edit_profile.html
│   └── change_password.html
└── tests/
    ├── test_all.py          # Feature tests (19 checks)
    ├── test_security.py     # Security tests  (9 checks)
    └── test_integration.py  # Integration tests (35 checks)
```

---

## Tech stack

- **Backend** — [FastAPI](https://fastapi.tiangolo.com/) with [Uvicorn](https://www.uvicorn.org/)
- **Database** — SQLite 3 via `sqlite3` stdlib (WAL mode, parameterized queries)
- **Templates** — [Jinja2](https://jinja.palletsprojects.com/) with auto-escaping
- **Markdown** — [markdown2](https://github.com/trentm/python-markdown2) with `safe_mode='escape'`
- **Fonts** — [Orbitron](https://fonts.google.com/specimen/Orbitron) + [Share Tech Mono](https://fonts.google.com/specimen/Share+Tech+Mono) (Google Fonts)
- **Avatars** — [Robohash](https://robohash.org/) (set 4)
