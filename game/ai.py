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

def _row_col_to_xy(row: int, col: int, size: int = BOARD_SIZE) -> tuple[int, int]:
    # Board row 0 is top; requested coordinate system is bottom-left origin.
    return (col, size - 1 - row)


def _xy_to_row_col(x: int, y: int, size: int = BOARD_SIZE) -> tuple[int, int]:
    return (size - 1 - y, x)


def _stone_lists_xy(board: list[list[int]]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    black_stones: list[tuple[int, int]] = []
    white_stones: list[tuple[int, int]] = []
    size = len(board)
    for row, row_vals in enumerate(board):
        for col, val in enumerate(row_vals):
            xy = _row_col_to_xy(row, col, size=size)
            if val == PLAYER:
                black_stones.append(xy)
            elif val == AI:
                white_stones.append(xy)
    return black_stones, white_stones


def _format_tuple_list(points: list[tuple[int, int]]) -> str:
    return "[" + ", ".join(f"({x}, {y})" for x, y in points) + "]"


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


def choose_ai_move(board: list[list[int]]) -> tuple[int, int, bool]:
    """
    Returns (row, col, saw_illegal_move) for AI move.
    Falls back to a random legal move if API fails or outputs invalid JSON.
    """
    moves = available_moves(board)
    _log(f"has_moves={bool(moves)}")
    if not moves:
        _log("branch=no_legal_moves")
        return (0, 0, False)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    _log(f"has_key={bool(api_key)} model={os.getenv('OPENAI_MODEL','gpt-4o-mini')}")

    if not api_key:
        _log("branch=fallback_random (missing key)")
        r, c = random.choice(moves)
        return (r, c, False)

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    size = len(board)
    black_stones, white_stones = _stone_lists_xy(board)
    legal_moves_xy = [_row_col_to_xy(r, c, size=size) for r, c in moves]

    system = (
        "You are the white player AI in Gomoku on a 15x15 board.\n"
        "Coordinate system:\n"
        "- A stone position is a tuple (x, y).\n"
        "- Origin is bottom-left, so bottom-left is (0, 0).\n"
        "- x increases to the right, y increases upward.\n"
        "Game rules:\n"
        "- Black and white alternate turns.\n"
        "- A player wins by making 5 consecutive stones in one straight line.\n"
        "- Straight lines include horizontal, vertical, and both diagonal directions.\n"
        "Goal:\n"
        "- Choose the best move for white to win the game.\n"
        "- If black has 3 or 4 connected stones in a line, prioritize blocking that line "
        "to prevent black from extending to 5.\n"
        "Output format:\n"
        "- Return ONLY JSON with keys x and y.\n"
        "- x and y must be integers in [0, 14].\n"
        "- The move must be one of the provided legal empty moves.\n"
        "- Example: {\"x\": 7, \"y\": 7}\n"
        "Do not include any extra text."
    )
    user = (
        "Current game state:\n"
        f"black_stones = {_format_tuple_list(black_stones)}\n"
        f"white_stones = {_format_tuple_list(white_stones)}\n"
        f"legal_moves_xy = {_format_tuple_list(legal_moves_xy)}\n\n"
        "Meaning:\n"
        "- black_stones and white_stones are Python lists.\n"
        "- Each item is a tuple (x, y) of an already placed stone.\n"
        "- legal_moves_xy lists all currently legal empty positions.\n\n"
        "Now choose exactly one move for white."
    )

    saw_illegal_move = False
    try:
        client = OpenAI(api_key=api_key)
        max_illegal_retries = 10
        retry_note = ""

        for attempt in range(1, max_illegal_retries + 1):
            user_input = user + retry_note
            resp = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_input},
                ],
            )

            text = (resp.output_text or "").strip()
            _log(f"attempt={attempt} openai_raw_text={text[:120]!r}")

            obj = _extract_json_obj(text)
            if not obj:
                _log("branch=fallback_random (no json parsed)")
                r, c = random.choice(moves)
                return (r, c, saw_illegal_move)

            if "x" in obj and "y" in obj:
                x, y = obj["x"], obj["y"]
            elif "row" in obj and "col" in obj:
                row_legacy, col_legacy = obj["row"], obj["col"]
                if not isinstance(row_legacy, int) or not isinstance(col_legacy, int):
                    _log("branch=fallback_random (legacy row/col not int)")
                    r, c = random.choice(moves)
                    return (r, c, saw_illegal_move)
                x, y = _row_col_to_xy(row_legacy, col_legacy, size=size)
            else:
                _log("branch=fallback_random (json missing keys)")
                r, c = random.choice(moves)
                return (r, c, saw_illegal_move)

            if not isinstance(x, int) or not isinstance(y, int):
                _log("branch=fallback_random (x/y not int)")
                r, c = random.choice(moves)
                return (r, c, saw_illegal_move)

            if x < 0 or x >= size or y < 0 or y >= size:
                _log("branch=fallback_random (x/y out of bounds)")
                r, c = random.choice(moves)
                return (r, c, saw_illegal_move)

            row, col = _xy_to_row_col(x, y, size=size)
            if (row, col) not in moves:
                saw_illegal_move = True
                if attempt < max_illegal_retries:
                    _log(
                        f"branch=illegal_move_retry attempt={attempt}/{max_illegal_retries} "
                        f"move_xy=({x},{y})"
                    )
                    retry_note = (
                        "\n\nYour previous move was illegal because it was not in legal_moves_xy. "
                        "Choose a different move strictly from legal_moves_xy."
                    )
                    continue
                _log(f"branch=fallback_random (illegal move after {max_illegal_retries} attempts)")
                r, c = random.choice(moves)
                return (r, c, saw_illegal_move)

            _log(f"branch=openai_success attempt={attempt} move_xy=({x},{y}) move_row_col=({row},{col})")
            return (row, col, saw_illegal_move)

        _log("branch=fallback_random (retry loop exhausted)")
        r, c = random.choice(moves)
        return (r, c, saw_illegal_move)

    except Exception as e:
        _log(f"branch=fallback_random (exception={type(e).__name__}: {e})")
        if DEBUG_AI:
            traceback.print_exc()
        r, c = random.choice(moves)
        return (r, c, saw_illegal_move)
