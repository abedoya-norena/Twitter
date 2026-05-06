import sqlite3
import re
import markdown2
from markupsafe import Markup
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from translations import TRANSLATIONS

DB = 'twitter_clone.db'
PER_PAGE = 50

app = FastAPI(debug=True)
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


def get_db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def get_lang(request):
    lang = request.cookies.get('lang', 'en')
    return lang if lang in TRANSLATIONS else 'en'


def render(request, template, ctx={}):
    ctx = dict(ctx)
    lang = get_lang(request)
    ctx.setdefault('t', TRANSLATIONS[lang])
    ctx.setdefault('lang', lang)
    return templates.TemplateResponse(request, template, ctx)


URL_RE = re.compile(r'(?<!\()(https?://[^\s<>"\)\]]+)')

def process_message(text):
    text = str(text)
    text = URL_RE.sub(r'[\1](\1)', text)
    text = re.sub(r'@(\w+)', r'[@\1](/user/\1)', text)
    html = markdown2.markdown(text, extras=['strike'])
    return Markup(html)


def enrich(rows):
    msgs = [dict(r) for r in rows]
    for m in msgs:
        m['message_html'] = process_message(m['message'])
    return msgs


def delete_thread(cur, message_id):
    cur.execute('SELECT id FROM messages WHERE reply_to = ?', [message_id])
    for row in cur.fetchall():
        delete_thread(cur, row['id'])
    cur.execute('DELETE FROM messages WHERE id = ?', [message_id])


def get_replies(con, parent_id):
    cur = con.cursor()
    cur.execute('''
        SELECT m.id, m.message, m.created_at, m.edited_at, m.reply_to, u.username, u.age,
               (SELECT count(*) FROM messages r WHERE r.reply_to = m.id) as reply_count
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.reply_to = ?
        ORDER BY m.created_at ASC
    ''', [parent_id])
    replies = enrich(cur.fetchall())
    for r in replies:
        r['replies'] = get_replies(con, r['id'])
    return replies


@app.get('/set_lang', response_class=HTMLResponse)
def set_lang(request: Request, lang: str = Query('en'), next: str = Query('/')):
    if lang not in TRANSLATIONS:
        lang = 'en'
    resp = RedirectResponse(url=next, status_code=303)
    resp.set_cookie('lang', lang, max_age=60 * 60 * 24 * 365)
    return resp


@app.get('/', response_class=HTMLResponse)
def root(request: Request, page: int = Query(1, ge=1)):
    username = request.cookies.get('username')
    offset = (page - 1) * PER_PAGE
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id, m.message, m.created_at, m.edited_at, u.username, u.age,
               (SELECT count(*) FROM messages r WHERE r.reply_to = m.id) as reply_count
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.reply_to IS NULL
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    ''', [PER_PAGE, offset])
    messages = enrich(cur.fetchall())
    total = con.execute('SELECT count(*) FROM messages WHERE reply_to IS NULL').fetchone()[0]
    con.close()
    return render(request, 'index.html', {
        'messages': messages,
        'username': username,
        'page': page,
        'total_pages': (total + PER_PAGE - 1) // PER_PAGE,
    })


@app.get('/messages/json')
def messages_json(page: int = Query(1, ge=1)):
    offset = (page - 1) * PER_PAGE
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id, m.message, m.created_at, m.edited_at, u.username, u.age
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.reply_to IS NULL
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    ''', [PER_PAGE, offset])
    rows = [dict(r) for r in cur.fetchall()]
    total = con.execute('SELECT count(*) FROM messages WHERE reply_to IS NULL').fetchone()[0]
    con.close()
    return JSONResponse({'page': page, 'total': total, 'messages': rows})


@app.get('/search', response_class=HTMLResponse)
def search(request: Request, q: str = Query(''), page: int = Query(1, ge=1)):
    username = request.cookies.get('username')
    offset = (page - 1) * PER_PAGE
    messages = []
    total_pages = 1
    if q.strip():
        like = f'%{q}%'
        con = get_db()
        cur = con.cursor()
        cur.execute('''
            SELECT m.id, m.message, m.created_at, m.edited_at, u.username, u.age,
                   (SELECT count(*) FROM messages r WHERE r.reply_to = m.id) as reply_count
            FROM messages m JOIN users u ON m.sender_id = u.id
            WHERE m.message LIKE ? OR u.username LIKE ?
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        ''', [like, like, PER_PAGE, offset])
        messages = enrich(cur.fetchall())
        total = con.execute('''
            SELECT count(*) FROM messages m JOIN users u ON m.sender_id = u.id
            WHERE m.message LIKE ? OR u.username LIKE ?
        ''', [like, like]).fetchone()[0]
        con.close()
        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    return render(request, 'search.html', {
        'username': username,
        'q': q,
        'messages': messages,
        'page': page,
        'total_pages': total_pages,
    })


@app.get('/login', response_class=HTMLResponse)
def login_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'login.html', {'username': username, 'tried': False, 'success': False})


@app.post('/login', response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT password FROM users WHERE username = ?', [username])
    row = cur.fetchone()
    con.close()
    success = row is not None and row['password'] == password
    if success:
        resp = RedirectResponse(url='/', status_code=303)
        resp.set_cookie('username', username)
        return resp
    return render(request, 'login.html', {'username': None, 'tried': True, 'success': False})


@app.get('/logout', response_class=HTMLResponse)
def logout(request: Request):
    resp = render(request, 'logout.html', {'username': None})
    resp.delete_cookie('username')
    return resp


@app.get('/create_message', response_class=HTMLResponse)
def create_message_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'create_message.html', {'username': username, 'posted': False})


@app.post('/create_message', response_class=HTMLResponse)
def create_message_submit(request: Request, message: str = Form(...)):
    username = request.cookies.get('username')
    if not username:
        return render(request, 'create_message.html', {
            'username': None, 'posted': False,
            'error': 'You must be logged in to post a message.',
        })
    if not message.strip():
        return render(request, 'create_message.html', {
            'username': username, 'posted': False,
            'error': 'Message cannot be empty.',
        })
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', [username])
    row = cur.fetchone()
    if row:
        cur.execute('INSERT INTO messages (sender_id, message) VALUES (?, ?)', [row['id'], message])
        con.commit()
    con.close()
    return RedirectResponse(url='/', status_code=303)


@app.get('/message/{message_id}', response_class=HTMLResponse)
def message_thread(request: Request, message_id: int):
    username = request.cookies.get('username')
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id, m.message, m.created_at, m.edited_at, m.reply_to, u.username, u.age,
               (SELECT count(*) FROM messages r WHERE r.reply_to = m.id) as reply_count
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.id = ?
    ''', [message_id])
    row = cur.fetchone()
    if not row:
        con.close()
        return RedirectResponse(url='/', status_code=303)
    msg = enrich([row])[0]
    msg['replies'] = get_replies(con, message_id)
    con.close()
    return render(request, 'thread.html', {'username': username, 'msg': msg})


@app.post('/reply/{parent_id}', response_class=HTMLResponse)
def post_reply(request: Request, parent_id: int, message: str = Form(...)):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    if not message.strip():
        return RedirectResponse(url=f'/message/{parent_id}', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', [username])
    user = cur.fetchone()
    cur.execute('SELECT id FROM messages WHERE id = ?', [parent_id])
    parent = cur.fetchone()
    if user and parent:
        cur.execute(
            'INSERT INTO messages (sender_id, message, reply_to) VALUES (?, ?, ?)',
            [user['id'], message, parent_id]
        )
        con.commit()
    con.close()
    return RedirectResponse(url=f'/message/{parent_id}', status_code=303)


@app.get('/edit_message/{message_id}', response_class=HTMLResponse)
def edit_message_form(request: Request, message_id: int):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id, m.message FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.id = ? AND u.username = ?
    ''', [message_id, username])
    row = cur.fetchone()
    con.close()
    if not row:
        return RedirectResponse(url='/', status_code=303)
    return render(request, 'edit_message.html', {'username': username, 'msg': dict(row)})


@app.post('/edit_message/{message_id}', response_class=HTMLResponse)
def edit_message_submit(request: Request, message_id: int, message: str = Form(...)):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.id = ? AND u.username = ?
    ''', [message_id, username])
    if cur.fetchone() and message.strip():
        cur.execute(
            "UPDATE messages SET message = ?, edited_at = datetime('now') WHERE id = ?",
            [message, message_id]
        )
        con.commit()
    con.close()
    return RedirectResponse(url='/', status_code=303)


@app.post('/delete_message/{message_id}', response_class=HTMLResponse)
def delete_message(request: Request, message_id: int):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        SELECT m.id FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.id = ? AND u.username = ?
    ''', [message_id, username])
    if cur.fetchone():
        delete_thread(cur, message_id)
        con.commit()
    con.close()
    referer = request.headers.get('referer', '/')
    return RedirectResponse(url=referer, status_code=303)


@app.get('/create_user', response_class=HTMLResponse)
def create_user_form(request: Request):
    username = request.cookies.get('username')
    return render(request, 'create_user.html', {'username': username, 'created': False})


@app.post('/create_user', response_class=HTMLResponse)
def create_user_submit(
    request: Request,
    new_username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    age: str = Form('')
):
    username = request.cookies.get('username')
    if password != password2:
        return render(request, 'create_user.html', {
            'username': username, 'created': False,
            'error': 'Passwords do not match.', 'new_username': new_username,
        })
    age_val = int(age) if age.strip().isdigit() else None
    error = None
    con = get_db()
    try:
        con.execute(
            'INSERT INTO users (username, password, age) VALUES (?, ?, ?)',
            [new_username, password, age_val]
        )
        con.commit()
    except sqlite3.IntegrityError:
        error = f'Username "{new_username}" is already taken.'
    finally:
        con.close()
    if error:
        return render(request, 'create_user.html', {
            'username': username, 'created': False,
            'error': error, 'new_username': new_username,
        })
    resp = RedirectResponse(url='/', status_code=303)
    resp.set_cookie('username', new_username)
    return resp


@app.get('/change_password', response_class=HTMLResponse)
def change_password_form(request: Request):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    return render(request, 'change_password.html', {'username': username})


@app.post('/change_password', response_class=HTMLResponse)
def change_password_submit(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    error = None
    success = False
    if new_password != new_password2:
        error = 'New passwords do not match.'
    elif not new_password.strip():
        error = 'New password cannot be empty.'
    else:
        con = get_db()
        cur = con.cursor()
        cur.execute('SELECT password FROM users WHERE username = ?', [username])
        row = cur.fetchone()
        if not row or row['password'] != old_password:
            error = 'Current password is incorrect.'
        else:
            cur.execute('UPDATE users SET password = ? WHERE username = ?', [new_password, username])
            con.commit()
            success = True
        con.close()
    return render(request, 'change_password.html', {
        'username': username, 'error': error, 'success': success,
    })


@app.post('/delete_user', response_class=HTMLResponse)
def delete_user(request: Request):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', [username])
    row = cur.fetchone()
    if row:
        cur.execute('DELETE FROM messages WHERE sender_id = ?', [row['id']])
        cur.execute('DELETE FROM users WHERE id = ?', [row['id']])
        con.commit()
    con.close()
    resp = RedirectResponse(url='/', status_code=303)
    resp.delete_cookie('username')
    return resp


@app.get('/user/{profile_username}', response_class=HTMLResponse)
def user_profile(request: Request, profile_username: str, page: int = Query(1, ge=1)):
    username = request.cookies.get('username')
    offset = (page - 1) * PER_PAGE
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT id, username, age, bio FROM users WHERE username = ?', [profile_username])
    profile = cur.fetchone()
    if not profile:
        con.close()
        return render(request, 'profile.html', {
            'username': username, 'profile': None,
            'messages': [], 'page': 1, 'total_pages': 1,
        })
    profile = dict(profile)
    cur.execute('''
        SELECT m.id, m.message, m.created_at, m.edited_at, u.username, u.age,
               (SELECT count(*) FROM messages r WHERE r.reply_to = m.id) as reply_count
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE u.username = ? AND m.reply_to IS NULL
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    ''', [profile_username, PER_PAGE, offset])
    messages = enrich(cur.fetchall())
    total = con.execute(
        'SELECT count(*) FROM messages m JOIN users u ON m.sender_id = u.id WHERE u.username = ? AND m.reply_to IS NULL',
        [profile_username]
    ).fetchone()[0]
    con.close()
    return render(request, 'profile.html', {
        'username': username,
        'profile': profile,
        'messages': messages,
        'page': page,
        'total_pages': max(1, (total + PER_PAGE - 1) // PER_PAGE),
    })


@app.get('/edit_profile', response_class=HTMLResponse)
def edit_profile_form(request: Request):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT username, age, bio FROM users WHERE username = ?', [username])
    profile = dict(cur.fetchone())
    con.close()
    return render(request, 'edit_profile.html', {'username': username, 'profile': profile})


@app.post('/edit_profile', response_class=HTMLResponse)
def edit_profile_submit(request: Request, age: str = Form(''), bio: str = Form('')):
    username = request.cookies.get('username')
    if not username:
        return RedirectResponse(url='/login', status_code=303)
    age_val = int(age) if age.strip().isdigit() else None
    con = get_db()
    con.execute(
        'UPDATE users SET age = ?, bio = ? WHERE username = ?',
        [age_val, bio.strip() or None, username]
    )
    con.commit()
    con.close()
    return RedirectResponse(url=f'/user/{username}', status_code=303)
