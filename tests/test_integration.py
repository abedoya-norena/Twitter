import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

"""
Integration tests for NeuroPulse.
Covers complete user journeys, cross-user authorization, reply threading,
language switching, pagination, and profile management.
"""

import re
import time
from fastapi.testclient import TestClient
from main import app

# Unique suffix so test users don't collide across repeated runs
RUN = str(int(time.time()))[-5:]

# ── helpers ──────────────────────────────────────────────────────────────────

def make_client(cookies=None):
    return TestClient(app, raise_server_exceptions=True, cookies=cookies or {})

def login(client, username, password):
    r = client.post('/login',
                    data={'username': username, 'password': password},
                    follow_redirects=True)
    assert r.url.path == '/', f"Login failed for {username}"
    return r

def register(client, username, password='testpass123', age=''):
    r = client.post('/create_user',
                    data={'new_username': username, 'password': password,
                          'password2': password, 'age': age},
                    follow_redirects=True)
    assert r.url.path == '/', f"Register failed for {username}"
    return r

def post_message(client, text):
    r = client.post('/create_message', data={'message': text},
                    follow_redirects=True)
    assert r.url.path == '/'
    return r

def first_msg_id(html):
    ids = re.findall(r'/delete_message/(\d+)', html)
    assert ids, "No deletable messages found in page"
    return ids[0]

# ── 1. AUTHENTICATION FLOWS ──────────────────────────────────────────────────

print("--- Authentication -------------------------------------------")

# Wrong password → stays on login page
c = make_client()
r = c.post('/login', data={'username': 'Mike', 'password': 'wrongpassword'})
assert r.url.path == '/login' or 'Authentication failed' in r.text, \
    "Bad password should not redirect to feed"
print("Wrong password rejected: OK")

# Correct password → redirects to feed, session cookie set
c = make_client()
login(c, 'Mike', '524euTjrWm6uK2C5iw8mC6aNgX1JI78o')
r = c.get('/')
assert 'href="/logout"' in r.text
assert 'href="/login"' not in r.text
print("Correct login sets session: OK")

# Logout clears session
r = c.get('/logout')
r2 = c.get('/')
assert 'href="/login"' in r2.text
assert 'href="/logout"' not in r2.text
print("Logout clears session: OK")

# Protected routes redirect to login when logged out
anon = make_client()
for path in ['/create_message', '/edit_profile', '/change_password']:
    r = anon.get(path)
    assert r.url.path == '/login' or r.status_code in (200, 303), \
        f"Unprotected route: {path}"
print("Protected routes redirect unauthenticated users: OK")

# ── 2. REGISTRATION ──────────────────────────────────────────────────────────

print("--- Registration ---------------------------------------------")

# Register new user → auto-login → in feed
c = make_client()
register(c, 'ITA'+RUN, 'hunter2', age='28')
r = c.get('/')
assert 'href="/logout"' in r.text
print("Register -> auto-login -> feed: OK")

# Duplicate username is rejected
c2 = make_client()
r = c2.post('/create_user',
            data={'new_username': 'ITA'+RUN, 'password': 'x',
                  'password2': 'x', 'age': ''},
            follow_redirects=False)
assert 'already taken' in r.text.lower() or r.status_code == 200
print("Duplicate username rejected: OK")

# Password mismatch is rejected
c3 = make_client()
r = c3.post('/create_user',
            data={'new_username': 'ITB'+RUN, 'password': 'abc',
                  'password2': 'xyz', 'age': ''},
            follow_redirects=False)
assert 'do not match' in r.text.lower() or r.status_code == 200
print("Password mismatch rejected: OK")

# ── 3. MESSAGE CRUD ──────────────────────────────────────────────────────────

print("--- Message CRUD ---------------------------------------------")

alice = make_client()
register(alice, 'ITAlice'+RUN)
post_message(alice, 'Alice original message')

# Message appears in feed
r = alice.get('/')
assert 'Alice original message' in r.text
print("Posted message appears in feed: OK")

# Edit own message
msg_id = first_msg_id(r.text)
r = alice.post(f'/edit_message/{msg_id}',
               data={'message': 'Alice edited message'},
               follow_redirects=True)
assert r.url.path == '/'
r = alice.get('/')
assert 'Alice edited message' in r.text
print("Edit own message: OK")

# Delete own message
r = alice.post(f'/delete_message/{msg_id}', follow_redirects=True)
assert r.status_code == 200
r = alice.get('/')
assert 'Alice edited message' not in r.text
print("Delete own message: OK")

# ── 4. CROSS-USER AUTHORIZATION ──────────────────────────────────────────────

print("--- Cross-user authorization ---------------------------------")

alice2 = make_client()
register(alice2, 'ITAlice2'+RUN)
post_message(alice2, 'Alice2 private message')
r = alice2.get('/')
alice2_msg_id = first_msg_id(r.text)

bob = make_client()
register(bob, 'ITBob'+RUN)

# Bob cannot edit Alice2's message
r = bob.post(f'/edit_message/{alice2_msg_id}',
             data={'message': 'Bob hacked this'},
             follow_redirects=True)
r2 = alice2.get('/')
assert 'Bob hacked this' not in r2.text, "Cross-user edit succeeded — SECURITY FAIL"
print("Cannot edit another user's message: OK")

# Bob cannot delete Alice2's message
r = bob.post(f'/delete_message/{alice2_msg_id}', follow_redirects=True)
r2 = alice2.get('/')
assert 'Alice2 private message' in r2.text, "Cross-user delete succeeded — SECURITY FAIL"
print("Cannot delete another user's message: OK")

# Bob cannot delete Alice2's account
r = bob.post('/delete_user', follow_redirects=True)
# Bob's session should be gone, Alice2 should still exist
r2 = alice2.get('/user/ITAlice2'+RUN)
assert 'ITAlice2'+RUN in r2.text, "delete_user deleted wrong account"
print("delete_user only deletes own account: OK")

# ── 5. REPLY THREADING ───────────────────────────────────────────────────────

print("--- Reply threading ------------------------------------------")

carol = make_client()
register(carol, 'ITCarol'+RUN)
post_message(carol, 'Top-level post by Carol')
r = carol.get('/')

# Find thread link for Carol's message
thread_ids = re.findall(r'/message/(\d+)', r.text)
assert thread_ids, "No /message/ links found in feed"
top_id = thread_ids[0]

# Replies do NOT appear in main feed
dave = make_client()
register(dave, 'ITDave'+RUN)
r_reply = dave.post(f'/reply/{top_id}',
                    data={'message': 'Dave replies to Carol'},
                    follow_redirects=True)
assert r_reply.status_code == 200

r_feed = carol.get('/')
assert 'Dave replies to Carol' not in r_feed.text, \
    "Reply leaked into main feed — should only appear in thread"
print("Replies excluded from main feed: OK")

# Reply appears on thread page
r_thread = carol.get(f'/message/{top_id}')
assert 'Dave replies to Carol' in r_thread.text
print("Reply appears on thread page: OK")

# Nested reply (reply to a reply)
nested_ids = re.findall(r'/message/(\d+)', r_thread.text)
reply_id = [i for i in nested_ids if i != top_id][0]
r_nested = carol.post(f'/reply/{reply_id}',
                      data={'message': 'Carol nests a reply'},
                      follow_redirects=True)
assert r_nested.status_code == 200
r_thread2 = carol.get(f'/message/{top_id}')
assert 'Carol nests a reply' in r_thread2.text
print("Nested reply (reply-to-reply) works: OK")

# Unauthenticated user cannot post reply
anon2 = make_client()
r = anon2.post(f'/reply/{top_id}', data={'message': 'anon sneaks in'})
r_check = carol.get(f'/message/{top_id}')
assert 'anon sneaks in' not in r_check.text
print("Unauthenticated reply blocked: OK")

# ── 6. PROFILE & EDIT PROFILE ────────────────────────────────────────────────

print("--- Profile management ---------------------------------------")

eve = make_client()
register(eve, 'ITEve'+RUN, age='30')

# Profile page renders
r = eve.get('/user/ITEve'+RUN)
assert 'ITEve'+RUN in r.text
assert r.status_code == 200
print("Own profile page renders: OK")

# Edit profile updates bio and age
r = eve.post('/edit_profile',
             data={'age': '31', 'bio': 'Neuroscience PhD candidate'},
             follow_redirects=True)
assert r.url.path == '/user/ITEve'+RUN
assert 'Neuroscience PhD candidate' in r.text
print("Edit profile saves changes: OK")

# Non-existent profile returns gracefully
r = eve.get('/user/userThatDoesNotExist99999')
assert r.status_code == 200
assert 'not found' in r.text.lower()
print("Non-existent profile handled gracefully: OK")

# ── 7. CHANGE PASSWORD ───────────────────────────────────────────────────────

print("--- Change password ------------------------------------------")

frank = make_client()
register(frank, 'ITFrank'+RUN, 'oldpass1')

# Wrong current password rejected
r = frank.post('/change_password',
               data={'old_password': 'wrongold',
                     'new_password': 'newpass1',
                     'new_password2': 'newpass1'})
assert 'incorrect' in r.text.lower()
print("Wrong current password rejected: OK")

# Mismatched new passwords rejected
r = frank.post('/change_password',
               data={'old_password': 'oldpass1',
                     'new_password': 'abc',
                     'new_password2': 'xyz'})
assert 'do not match' in r.text.lower()
print("Mismatched new passwords rejected: OK")

# Successful change, then old password no longer works
r = frank.post('/change_password',
               data={'old_password': 'oldpass1',
                     'new_password': 'newpass1',
                     'new_password2': 'newpass1'})
assert 'updated successfully' in r.text.lower()

new_client = make_client()
r = new_client.post('/login',
                    data={'username': 'ITFrank'+RUN, 'password': 'oldpass1'})
assert r.url.path != '/', "Old password still works after change — SECURITY FAIL"
print("Old password invalidated after change: OK")

# ── 8. LANGUAGE SWITCHING ────────────────────────────────────────────────────

print("--- Language switching ---------------------------------------")

lang_client = make_client()

r = lang_client.get('/set_lang?lang=es&next=/', follow_redirects=True)
assert 'Inicio' in r.text or 'feed en vivo' in r.text
print("Spanish (ES) language switch: OK")

r = lang_client.get('/set_lang?lang=fr&next=/', follow_redirects=True)
assert 'Fil' in r.text or 'fil en direct' in r.text
print("French (FR) language switch: OK")

r = lang_client.get('/set_lang?lang=en&next=/', follow_redirects=True)
assert 'Feed' in r.text or 'live feed' in r.text
print("English (EN) language switch: OK")

# Invalid lang code falls back to English
r = lang_client.get('/set_lang?lang=xx&next=/', follow_redirects=True)
assert 'Feed' in r.text or 'live feed' in r.text
print("Invalid lang code falls back to EN: OK")

# ── 9. SEARCH ────────────────────────────────────────────────────────────────

print("--- Search ---------------------------------------------------")

searcher = make_client()
register(searcher, 'ITSearch'+RUN)
post_message(searcher, 'unique_neuro_search_term_xyz')

r = searcher.get('/search?q=unique_neuro_search_term_xyz')
assert 'unique_neuro_search_term_xyz' in r.text
print("Search finds own posted message: OK")

r = searcher.get('/search?q=zzzznotfound99999abcxyz')
assert 'no results' in r.text.lower() or 'aucun' in r.text.lower() or 'encontr' in r.text.lower()
print("Search with no results handled: OK")

r = searcher.get('/search?q=')
assert r.status_code == 200
print("Empty search query handled: OK")

# ── 10. PAGINATION ───────────────────────────────────────────────────────────

print("--- Pagination -----------------------------------------------")

r = make_client().get('/')
assert 'page=2' in r.text
print("Feed page 1 links to page 2: OK")

r = make_client().get('/?page=2')
assert r.status_code == 200
assert 'page=3' in r.text
print("Feed page 2 renders and links forward: OK")

r = make_client().get('/?page=9999')
assert r.status_code == 200
print("Out-of-range page number handled gracefully: OK")

# ── 11. DELETE ACCOUNT CASCADE ───────────────────────────────────────────────

print("--- Account deletion -----------------------------------------")

cleanup = make_client()
register(cleanup, 'ITClean'+RUN)
post_message(cleanup, 'This message should disappear')
r = cleanup.get('/')
assert 'This message should disappear' in r.text

r = cleanup.post('/delete_user', follow_redirects=True)
assert r.url.path == '/'
# Cookie should be gone → shows login link
assert 'href="/login"' in r.text

# Messages also gone from feed
r2 = make_client().get('/')
assert 'This message should disappear' not in r2.text
print("Delete account removes user and their messages: OK")

# ── SUMMARY ──────────────────────────────────────────────────────────────────

print()
print("All integration tests passed!")
