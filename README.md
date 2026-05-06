# NeuroPulse

A neuro-themed Twitter clone built with FastAPI, SQLite, and Jinja2.

## Setup

```bash
# Install dependencies
pip install fastapi uvicorn jinja2 python-multipart aiofiles

# Create the database (first time only)
python db_create.py

# Run the dev server
uvicorn main:app --reload
```

Then open **http://127.0.0.1:8000**

## Routes

| Route | Description |
|---|---|
| `/` | Feed — all tweets, newest first |
| `/login` | Log in with username + password |
| `/logout` | Clear session cookie |
| `/create_message` | Post a new tweet (must be logged in) |
| `/create_user` | Register a new account |

## Project structure

```
TWITTER/
├── main.py              # FastAPI app (all routes)
├── db_create.py         # One-time DB setup script
├── twitter_clone.db     # SQLite database (generated)
├── templates/
│   ├── base.html        # Shared layout + nav
│   ├── index.html       # Feed (/)
│   ├── login.html       # /login
│   ├── logout.html      # /logout
│   ├── create_message.html  # /create_message
│   └── create_user.html     # /create_user
├── static/
│   ├── style.css        # Neuro-themed CSS
│   └── neuron.svg       # Neural network banner image
└── quiz/                # SQL practice problems
```

## Screenshot

![NeuroPulse feed](screenshot.png)

## Demo credentials

| Username | Password |
|---|---|
| Mike | `524euTjrWm6uK2C5iw8mC6aNgX1JI78o` |
| Trump | `Trump` |
| Biden | `Biden` |
