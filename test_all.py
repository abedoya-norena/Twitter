from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=True)

# Feed + pagination
r = client.get('/')
assert r.status_code == 200
assert 'NeuroPulse' in r.text
assert 'page=2' in r.text
print('Feed + pagination: OK')

# Page 2
r = client.get('/?page=2')
assert r.status_code == 200
assert 'page=3' in r.text
print('Page 2: OK')

# JSON endpoint
r = client.get('/messages/json')
assert r.status_code == 200
data = r.json()
assert 'messages' in data and len(data['messages']) == 50
assert 'total' in data
print('JSON endpoint: OK')

# Search
r = client.get('/search?q=python')
assert r.status_code == 200
assert 'python' in r.text.lower()
print('Search: OK')

# Search no results
r = client.get('/search?q=zzzznotfound12345')
assert 'No results' in r.text
print('Search no results: OK')

# Login redirect
r = client.post('/login', data={'username': 'Mike', 'password': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o'}, follow_redirects=True)
assert r.url.path == '/'
print('Login redirect: OK')

# Nav when logged in
assert 'href="/create_message"' in r.text
assert 'href="/logout"' in r.text
assert 'href="/login"' not in r.text
print('Nav (logged in): OK')

# Post tweet → redirects to feed
r = client.post('/create_message', data={'message': 'Hello extra credit!'}, follow_redirects=True)
assert r.url.path == '/'
r2 = client.get('/')
assert 'Hello extra credit!' in r2.text
print('Create message + redirect + on feed: OK')

# Robohash image in feed
assert 'robohash.org' in r2.text
print('Robohash images: OK')

# Markdown rendering
client.post('/create_message', data={'message': '**bold** and _italic_'})
r = client.get('/')
assert '<strong>bold</strong>' in r.text
print('Markdown rendering: OK')

# @mention rendering
client.post('/create_message', data={'message': 'Hey @Mike check this out'})
r = client.get('/')
assert 'href="/user/Mike"' in r.text
print('@mention links: OK')

# URL linkify
client.post('/create_message', data={'message': 'Visit https://python.org for more'})
r = client.get('/')
assert 'href="https://python.org"' in r.text
print('URL linkify: OK')

# Edit message
r = client.get('/edit_message/1')
assert r.status_code in (200, 303)
print('Edit message form: OK')

# Profile page
r = client.get('/user/Mike')
assert r.status_code == 200
assert '@Mike' in r.text
assert 'robohash.org' in r.text
print('Profile page: OK')

# Edit profile
r = client.post('/edit_profile', data={'age': '36', 'bio': 'Updated bio'}, follow_redirects=True)
assert r.status_code == 200
assert 'Updated bio' in r.text
print('Edit profile: OK')

# Change password
r = client.post('/change_password', data={
    'old_password': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o',
    'new_password': 'newpass123',
    'new_password2': 'newpass123',
})
assert 'updated successfully' in r.text.lower()
# Change it back
client.post('/change_password', data={
    'old_password': 'newpass123',
    'new_password': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o',
    'new_password2': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o',
})
print('Change password: OK')

# Register → auto-login → redirect to feed
r = client.post('/create_user', data={
    'new_username': 'AutoTest99',
    'password': 'pass123',
    'password2': 'pass123',
    'age': '25',
}, follow_redirects=True)
assert r.url.path == '/'
print('Auto-login after register: OK')

# Delete message (post one first as AutoTest99)
client.post('/create_message', data={'message': 'To be deleted'})
r = client.get('/')
import re
msg_ids = re.findall(r'/delete_message/(\d+)', r.text)
assert msg_ids
del_id = msg_ids[0]
r = client.post(f'/delete_message/{del_id}', follow_redirects=True)
assert r.status_code == 200
print('Delete message: OK')

# Delete account
r = client.post('/delete_user', follow_redirects=True)
assert r.url.path == '/'
r = client.get('/')
assert 'href="/login"' in r.text
print('Delete account: OK')

print()
print('All optional feature checks passed!')
