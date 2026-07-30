"""
views/auth.py
=============
Authentication Blueprint — exposes /register and /login.

Session strategy: JWT (JSON Web Token) returned in the response body and
expected on subsequent requests via the Authorization: Bearer <token> header.
The token payload carries user_id and username so the gatekeeper middleware
can reconstruct identity without a round-trip to the user store.
"""

import os
import jwt
import datetime
from flask import Blueprint, request, jsonify, current_app

from models.user import User, UserStore

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
_store = UserStore()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_token(user: User) -> str:
    """
    Encode a signed JWT that expires in 24 hours.

    Payload:
        sub  — user_id  (int)
        usr  — username (str)
        exp  — expiry   (UTC datetime)
        iat  — issued-at
    """
    secret = current_app.config["JWT_SECRET"]
    payload = {
        "sub": str(user.user_id),   # PyJWT 2.x requires sub as string
        "usr": user.username,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.

    Request body (JSON):
        {
            "username": "alice",
            "password": "s3cur3P@ss!"
        }

    Responses:
        201 — account created, JWT returned
        400 — missing fields or username already taken
    """
    body = request.get_json(silent=True) or {}

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    # --- Input validation ---
    if not username or not password:
        return jsonify({"error": "Both 'username' and 'password' are required."}), 400

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    # --- Uniqueness check ---
    if _store.find_by_username(username) is not None:
        return jsonify({"error": f"Username '{username}' is already taken."}), 400

    # --- Persist ---
    new_user = User.create(
        user_id=_store.next_id(),
        username=username,
        plain_password=password,
    )
    _store.save(new_user)

    token = _make_token(new_user)

    return jsonify({
        "message": "Account created successfully.",
        "user":    new_user.public_dict(),
        "token":   token,
    }), 201


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate an existing user and issue a JWT.

    Request body (JSON):
        {
            "username": "alice",
            "password": "s3cur3P@ss!"
        }

    Responses:
        200 — credentials valid, JWT returned
        400 — missing fields
        401 — invalid credentials
    """
    body = request.get_json(silent=True) or {}

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    # --- Input validation ---
    if not username or not password:
        return jsonify({"error": "Both 'username' and 'password' are required."}), 400

    # --- Credential check ---
    user = _store.find_by_username(username)
    if user is None or not user.verify_password(password):
        # Deliberately vague — do not reveal which field was wrong
        return jsonify({"error": "Invalid username or password."}), 401

    token = _make_token(user)

    return jsonify({
        "message": "Login successful.",
        "user":    user.public_dict(),
        "token":   token,
    }), 200
