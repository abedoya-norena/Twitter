'''
NeuroPulse — a FastAPI Twitter-clone CRUD app.
Run: uvicorn main:app --reload
'''
import sqlite3
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

DB = 'twitter_clone.db'

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def render(request: Request, template: str, ctx: dict = {}):
    return templates.TemplateResponse(request, template, ctx)


# ── / ──────────────────────────────────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
def root(request: Request):
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.message, m.created_at, u.username, u.age
        FROM   messages m
        JOIN   users    u ON m.sender_id = u.id
        ORDER  BY m.created_at DESC
    ''')
    messages = [dict(row) for row in cur.fetchall()]
    con.close()
    username = request.cookies.get('username')
    return render(request, 'index.html', {'messages': messages, 'username': username})


# ── /login ─────────────────────────────────────────────────────────────────────

@app.get('/login', response_class=HTMLResponse)
def login_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'login.html', {'username': username, 'tried': False, 'success': False})


@app.post('/login', response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT password FROM users WHERE username = ?', [username])
    row = cur.fetchone()
    con.close()

    success = row is not None and row['password'] == password

    resp = render(request, 'login.html', {
        'username': username if success else None,
        'tried': True,
        'success': success,
    })
    if success:
        resp.set_cookie('username', username)
    return resp


# ── /logout ────────────────────────────────────────────────────────────────────

@app.get('/logout', response_class=HTMLResponse)
def logout(request: Request):
    resp = render(request, 'logout.html', {'username': None})
    resp.delete_cookie('username')
    return resp


# ── /create_message ────────────────────────────────────────────────────────────

@app.get('/create_message', response_class=HTMLResponse)
def create_message_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'create_message.html', {'username': username, 'posted': False})


@app.post('/create_message', response_class=HTMLResponse)
def create_message_submit(
    request: Request,
    message: str = Form(...),
):
    username = request.cookies.get('username')
    error = None

    if not username:
        error = 'You must be logged in to post a message.'
    else:
        con = get_db()
        cur = con.cursor()
        cur.execute('SELECT id FROM users WHERE username = ?', [username])
        row = cur.fetchone()
        if row:
            cur.execute(
                'INSERT INTO messages (sender_id, message) VALUES (?, ?)',
                [row['id'], message]
            )
            con.commit()
        else:
            error = 'User not found.'
        con.close()

    return render(request, 'create_message.html', {
        'username': username,
        'posted': error is None,
        'error': error,
        'message': message,
    })


# ── /create_user ───────────────────────────────────────────────────────────────

@app.get('/create_user', response_class=HTMLResponse)
def create_user_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'create_user.html', {'username': username, 'created': False})


@app.post('/create_user', response_class=HTMLResponse)
def create_user_submit(
    request: Request,
    new_username: str = Form(...),
    password:     str = Form(...),
    age:          str = Form(''),
):
    username = request.cookies.get('username')
    error = None

    age_val = int(age) if age.strip().isdigit() else None
    try:
        con = get_db()
        cur = con.cursor()
        cur.execute(
            'INSERT INTO users (username, password, age) VALUES (?, ?, ?)',
            [new_username, password, age_val]
        )
        con.commit()
        con.close()
    except sqlite3.IntegrityError:
        error = f'Username "{new_username}" is already taken.'

    return render(request, 'create_user.html', {
        'username': username,
        'created': error is None,
        'error': error,
        'new_username': new_username,
    })
