import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from game.board import empty_board, apply_move, PLAYER, AI
from game.rules import check_winner, is_draw
from game.validate import parse_board, validate_move
from game.ai import choose_ai_move

app = Flask(__name__)

# MVP: allow all origins. You can restrict to your GitHub Pages origin later.
CORS(app, resources={r"/*": {"origins": "*"}})


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/start")
def start():
    board = empty_board()
    return jsonify({
        "board": board,
        "status": "ongoing",
        "message": "Game started. Your turn (black).",
    })


@app.post("/move")
def move():
    data = request.get_json(silent=True) or {}

    try:
        board = parse_board(data.get("board"))
        winner = check_winner(board)
        if winner == PLAYER:
            return jsonify({
                "board": board,
                "status": "player_win",
                "message": "Game already finished. You already won. Click New Game.",
            })
        if winner == AI:
            return jsonify({
                "board": board,
                "status": "ai_win",
                "message": "Game already finished. AI already won. Click New Game.",
            })
        if is_draw(board):
            return jsonify({
                "board": board,
                "status": "draw",
                "message": "Game already finished in a draw. Click New Game.",
            })

        row = data.get("row")
        col = data.get("col")
        validate_move(board, row, col)

        # Player move
        apply_move(board, row, col, PLAYER)

        winner = check_winner(board)
        if winner == PLAYER:
            return jsonify({
                "board": board,
                "status": "player_win",
                "message": "You win!",
            })

        if is_draw(board):
            return jsonify({
                "board": board,
                "status": "draw",
                "message": "Draw.",
            })

        # AI move
        ai_r, ai_c, saw_illegal_move = choose_ai_move(board)
        ai_warning = "AI gives an illegal move." if saw_illegal_move else None
        validate_move(board, ai_r, ai_c)
        apply_move(board, ai_r, ai_c, AI)

        winner = check_winner(board)
        if winner == AI:
            return jsonify({
                "board": board,
                "ai_move": [ai_r, ai_c],
                "ai_warning": ai_warning,
                "status": "ai_win",
                "message": "AI wins.",
            })

        if is_draw(board):
            return jsonify({
                "board": board,
                "ai_move": [ai_r, ai_c],
                "ai_warning": ai_warning,
                "status": "draw",
                "message": "Draw.",
            })

        return jsonify({
            "board": board,
            "ai_move": [ai_r, ai_c],
            "ai_warning": ai_warning,
            "status": "ongoing",
            "message": "Your turn.",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        # Don’t leak internals; keep it stable for grading
        return jsonify({"error": "server_error"}), 500


if __name__ == "__main__":
    # Local dev only. Render uses gunicorn.
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
