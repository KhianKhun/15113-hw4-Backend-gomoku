import json
import os
import random
import re
from typing import Optional

from openai import OpenAI

from .board import BOARD_SIZE, AI, PLAYER, available_moves

# OpenAI client reads OPENAI_API_KEY from env by default; explicit is also fine.
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def _board_to_compact_text(board: list[list[int]]) -> str:
    # 0 empty, 1 player, 2 AI; keep it compact for tokens
    return "\n".join(" ".join(str(x) for x in row) for row in board)


def _extract_json_obj(text: str) -> Optional[dict]:
    # Try raw JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def choose_ai_move(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns (row, col) for AI move.
    Falls back to a random legal move if API fails or outputs invalid JSON.
    """
    moves = available_moves(board)
    if not moves:
        # should be draw, but just in case
        return (0, 0)

    # Simple “opening” heuristic: prefer center if empty
    center = BOARD_SIZE // 2
    if board[center][center] == 0:
        return (center, center)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return random.choice(moves)

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    system = (
        "You are an AI opponent playing Gomoku (five-in-a-row) on a 15x15 board.\n"
        "Board encoding:\n"
        "  0 = empty, 1 = human (black), 2 = AI (white)\n"
        "Return ONLY valid JSON with keys row and col (0-14), choosing an empty cell.\n"
        "Example: {\"row\": 7, \"col\": 7}\n"
        "Do not include any extra text."
    )

    user = (
        "Current board (15 rows of 15 ints):\n"
        f"{_board_to_compact_text(board)}\n\n"
        "It's AI's turn (2). Pick a good move."
    )

    try:
        # Use Responses API (recommended for new projects). :contentReference[oaicite:1]{index=1}
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = (resp.output_text or "").strip()
        obj = _extract_json_obj(text)
        if not obj or "row" not in obj or "col" not in obj:
            return random.choice(moves)

        row, col = obj["row"], obj["col"]
        if not isinstance(row, int) or not isinstance(col, int):
            return random.choice(moves)
        if (row, col) not in moves:
            return random.choice(moves)

        return (row, col)

    except Exception:
        # Network / API errors -> fallback
        return random.choice(moves)
