"""
middleware/auth_guard.py
========================
Profile Gatekeeper — the @token_required decorator.

Any route that needs a verified, logged-in user should be wrapped with this
decorator.  It validates the JWT from the Authorization header, decodes the
payload, looks up the matching User record, and injects the live User object
into the wrapped function as the first positional argument `current_user`.

Usage
-----
    from middleware.auth_guard import token_required

    @posts_bp.route("/posts/<int:post_id>", methods=["DELETE"])
    @token_required
    def delete_post(current_user, post_id):
        # current_user is the authenticated User object
        ...

Error responses
---------------
    401  Missing Authorization header
    401  Token has expired
    401  Token is invalid / tampered
    401  User referenced in token no longer exists
"""

import jwt
from functools import wraps
from flask import request, jsonify, current_app

from models.user import UserStore

_store = UserStore()


def token_required(f):
    """
    Decorator that enforces JWT authentication on a Flask route.

    The decorator:
        1. Extracts the Bearer token from the Authorization header.
        2. Decodes and verifies the JWT signature and expiry.
        3. Fetches the corresponding User from the store.
        4. Passes the User as `current_user` to the wrapped view function.

    Rejects the request with HTTP 401 if any step fails.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # --- 1. Extract token from header ---
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({
                "error": "Authentication required. "
                         "Provide a Bearer token in the Authorization header."
            }), 401

        # --- 2. Decode & verify JWT ---
        secret = current_app.config["JWT_SECRET"]
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token. Authentication failed."}), 401

        # --- 3. Confirm user still exists in the store ---
        user_id = payload.get("sub")
        current_user = _store.find_by_id(user_id)

        if current_user is None:
            return jsonify({
                "error": "User account not found. Token is no longer valid."
            }), 401

        # --- 4. Delegate to the actual view with the resolved user ---
        return f(current_user, *args, **kwargs)

    return decorated


def owner_required(resource_owner_id_fn):
    """
    Decorator factory that extends @token_required to also check that
    the authenticated user owns the resource they are trying to modify.

    Parameters
    ----------
    resource_owner_id_fn : callable
        A function that receives the same *args/**kwargs as the route and
        returns the owner_id (int) of the resource.  Returning None skips
        the ownership check (treat as 404 upstream).

    Usage
    -----
        def _get_post_owner(post_id):
            # look up post and return post.owner_id
            ...

        @posts_bp.route("/posts/<int:post_id>", methods=["PUT"])
        @owner_required(_get_post_owner)
        def update_post(current_user, post_id):
            ...
    """

    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            owner_id = resource_owner_id_fn(*args, **kwargs)
            if owner_id is not None and current_user.user_id != owner_id:
                return jsonify({
                    "error": "Forbidden. You do not own this resource."
                }), 403
            return f(current_user, *args, **kwargs)

        return decorated

    return decorator
