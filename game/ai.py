import json
import os
import random
import re
import traceback
from typing import Optional

from openai import OpenAI

from .board import BOARD_SIZE, AI, PLAYER, available_moves

DEBUG_AI = os.getenv("AI_DEBUG", "0") == "1"

def _log(msg: str):
    if DEBUG_AI:
        print(f"[AI_DEBUG] {msg}", flush=True)

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
    _log(f"has_moves={bool(moves)}")
    if not moves:
        _log("branch=no_legal_moves")
        return (0, 0)

    center = BOARD_SIZE // 2
    if board[center][center] == 0:
        _log("branch=center_heuristic")
        return (center, center)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    _log(f"has_key={bool(api_key)} model={os.getenv('OPENAI_MODEL','gpt-4o-mini')}")

    if not api_key:
        _log("branch=fallback_random (missing key)")
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
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        text = (resp.output_text or "").strip()
        _log(f"openai_raw_text={text[:120]!r}")

        obj = _extract_json_obj(text)
        if not obj:
            _log("branch=fallback_random (no json parsed)")
            return random.choice(moves)

        if "row" not in obj or "col" not in obj:
            _log("branch=fallback_random (json missing keys)")
            return random.choice(moves)

        row, col = obj["row"], obj["col"]
        if not isinstance(row, int) or not isinstance(col, int):
            _log("branch=fallback_random (row/col not int)")
            return random.choice(moves)

        if (row, col) not in moves:
            _log("branch=fallback_random (illegal move)")
            return random.choice(moves)

        _log("branch=openai_success")
        return (row, col)

    except Exception as e:
        _log(f"branch=fallback_random (exception={type(e).__name__}: {e})")
        if DEBUG_AI:
            traceback.print_exc()
        return random.choice(moves)

