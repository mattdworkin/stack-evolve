from flask import Flask, jsonify, request, abort

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    q = request.args.get("q")
    if user_id < 0:
        abort(404)
    return jsonify({"user_id": user_id, "q": q}), 200