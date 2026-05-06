# NeuroPulse

[![Tests](https://github.com/abedoya-norena/Twitter/actions/workflows/tests.yml/badge.svg)](https://github.com/abedoya-norena/Twitter/actions/workflows/tests.yml)
[![FastAPI](https://img.shields.io/pypi/v/fastapi?style=flat-square&logo=fastapi&logoColor=white&label=FastAPI&color=009688)](https://pypi.org/project/fastapi/)
![i18n](https://img.shields.io/badge/i18n-EN%20%7C%20ES%20%7C%20FR-blueviolet?style=flat-square)

A Twitter clone themed around decision neuroscience. 200 simulated researchers posting fMRI takes.

![NeuroPulse feed](Neuro_Image.png)

## Setup

```bash
pip install -r requirements.txt
python db_create.py
uvicorn main:app --reload
```

http://127.0.0.1:8000

## Test accounts

| Username | Password |
|---|---|
| `Mike` | `524euTjrWm6uK2C5iw8mC6aNgX1JI78o` |
| `Trump` | `Trump` |
| `Biden` | `Biden` |
| `Evan` | `correct horse battery staple` |
| `Kristen` | `Possible-Rich-Absolute-Battle` |

## Tests

```bash
python tests/test_check.py       # smoke
python tests/test_all.py         # features
python tests/test_security.py    # SQL injection, XSS, auth bypass
python tests/test_integration.py # full user journeys
```

Also runs on push via GitHub Actions.
