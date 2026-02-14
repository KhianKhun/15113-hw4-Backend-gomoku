# Gomoku Backend (Flask + Render)

This backend validates moves, maintains game progression, and generates AI responses for the web Gomoku frontend.

## What This Backend Does

### Board encoding
- `0` = empty
- `1` = human player (black)
- `2` = AI player (white)

### Endpoints

#### `GET /health`
Health check endpoint for local/devops monitoring.

Response example:
```json
{ "ok": true }
```

#### `POST /start`
Creates and returns a fresh 15x15 board.

Request body:
```json
{}
```

Response example:
```json
{
  "board": [[0,0,0], [0,0,0], [0,0,0]],
  "status": "ongoing",
  "message": "Game started. Your turn (black)."
}
```

#### `POST /move`
Accepts one player move, validates it, updates board state, checks win/draw, asks AI for a response move, and returns the updated board.

Request body:
```json
{
  "board": [[0,0,0], [0,0,0], [0,0,0]],
  "row": 7,
  "col": 7
}
```

Validation behavior:
- board must be a valid 15x15 matrix with values only in `{0,1,2}`
- `row` and `col` must be integers in bounds
- move must target an empty cell
- if submitted board is already terminal (`player_win`, `ai_win`, `draw`), backend returns terminal status and does not continue playing

Possible response fields:
- `board`: updated board after player/AI moves
- `status`: `ongoing | player_win | ai_win | draw`
- `message`: human-readable status
- `ai_move`: `[row, col]` when AI moved
- `ai_warning`: warning text when AI produced illegal coordinates and fallback was used

Error responses:
- `400` with `{"error": "..."}` for invalid request data
- `500` with `{"error": "server_error"}` for unexpected server failures

## How Frontend Communicates With Backend

Frontend (GitHub Pages) flow:
1. On initial load and on **New Game**, frontend calls `POST /start`.
2. Frontend renders returned `board`, updates status message, and unlocks interaction.
3. On player click, frontend sends `POST /move` with current board + selected row/col.
4. Frontend updates UI using response:
- redraws board from returned `board`
- updates message from `status/message`
- displays AI warning when `ai_warning` exists
- blocks further interaction when `status` is terminal

## Local Setup And Run

### 1) Create and activate a virtual environment
```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure local environment variables
Create `.env` in repo root:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
AI_DEBUG=0
```

### 4) Run backend locally
```bash
python app.py
```

Local server:
- `http://127.0.0.1:5000`

## Authentication And Secret Handling

- OpenAI API credentials are stored **only on backend** through environment variables.
- Frontend code never contains or exposes the OpenAI API key.
- `.env` is excluded from git via `.gitignore`.
- In Render, secrets should be set in service **Environment Variables**, not committed to code.

## Render Deployment Notes

Recommended Render commands:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`

Recommended Render env vars:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional; default `gpt-4o-mini`)
- `AI_DEBUG` (optional; default `0`)