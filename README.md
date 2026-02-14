# Gomoku Backend (Flask + Render)

## What this backend does
Endpoints:
- `GET /health` -> `{ ok: true }`
- `POST /start` -> returns a fresh 15x15 board
- `POST /move` -> accepts `{ board, row, col }`, validates the player move, checks win/draw,
  calls OpenAI to select an AI move, returns updated board + status.

Board encoding:
- 0 = empty
- 1 = human (black)
- 2 = AI (white)

## Frontend communication
The frontend (GitHub Pages) calls:
- `/start` when the page loads or when the user clicks "New Game"
- `/move` after the user clicks a cell (row/col)

Responses are JSON and include updated `board` and a `status` string.

## Local setup
```bash
python -m venv .venv
# activate venv...
pip install -r requirements.txt
cp .env.example .env
# put your OPENAI_API_KEY in .env
python app.py
