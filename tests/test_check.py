import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app
client = TestClient(app, raise_server_exceptions=True)

# 1. Feed loads
r = client.get('/')
assert r.status_code == 200
print('Feed: OK')

# 2. Nav logged out - Login/Register visible, Tweet/Logout hidden
assert 'href="/login"' in r.text
assert 'href="/create_user"' in r.text
assert 'href="/create_message"' not in r.text
assert 'href="/logout"' not in r.text
print('Nav (logged out): OK')

# 3. Wrong password shows error
r = client.post('/login', data={'username': 'Mike', 'password': 'wrong'})
assert r.status_code == 200
assert 'failed' in r.text.lower() or 'Authentication' in r.text
print('Login bad password: OK')

# 4. Good login redirects to /
r = client.post('/login', data={'username': 'Mike', 'password': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o'}, follow_redirects=True)
assert r.url.path == '/'
print('Login redirect to feed: OK')

# 5. Nav logged in - Tweet/Logout visible, Login/Register hidden
assert 'href="/create_message"' in r.text
assert 'href="/logout"' in r.text
assert 'href="/login"' not in r.text
assert 'href="/create_user"' not in r.text
print('Nav (logged in): OK')

# 6. Password mismatch on register
r = client.post('/create_user', data={'new_username': 'TestUser', 'password': 'abc', 'password2': 'xyz', 'age': ''})
assert 'do not match' in r.text.lower()
print('Password mismatch: OK')

# 7. Duplicate username
r = client.post('/create_user', data={'new_username': 'Mike', 'password': 'abc', 'password2': 'abc', 'age': ''})
assert 'already taken' in r.text.lower()
print('Duplicate username: OK')

# 8. Post message and verify it shows on feed
client.post('/create_message', data={'message': 'Hello from the test!'})
feed = client.get('/')
assert 'Hello from the test!' in feed.text
print('Create message shows on feed: OK')

print()
print('All checks passed!')
