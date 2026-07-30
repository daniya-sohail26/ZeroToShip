"""
app.py
======
TradePost — Phase 2 server entry point.

Responsibilities
----------------
* Bootstrap the Flask application.
* Load configuration (JWT secret, debug flag) from environment variables
  with safe defaults for local development.
* Register the authentication Blueprint (views/auth.py).
* Provide a /health liveness endpoint so Postman/CI can verify the server
  is up without needing credentials.
* Run the development server when executed directly.

Environment variables
---------------------
    JWT_SECRET   — signing key for JWTs          (default: dev-only fallback)
    FLASK_DEBUG  — "1" to enable debug/reload    (default: "0")
    PORT         — port to bind                  (default: 5000)
"""

import os
from flask import Flask, jsonify

from views.auth import auth_bp
from views.routes import api_bp


def create_app() -> Flask:
    """
    Application factory.

    Using a factory function (rather than a module-level app instance) makes
    the app easy to test and allows multiple configurations to coexist.
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    # JWT_SECRET must be set to a long random string in production.
    # The fallback value is intentionally weak to signal misconfiguration.
    app.config["JWT_SECRET"] = os.environ.get(
        "JWT_SECRET", "CHANGE_ME_before_deploying_to_production"
    )

    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

    # ------------------------------------------------------------------
    # Blueprint registration
    # ------------------------------------------------------------------

    app.register_blueprint(auth_bp)          # /auth/register, /auth/login
    app.register_blueprint(api_bp)           # /api/posts, /api/offers, ...

    # ------------------------------------------------------------------
    # Core routes
    # ------------------------------------------------------------------

    @app.route("/health", methods=["GET"])
    def health():
        """
        Liveness check — no authentication required.
        Useful for Postman smoke tests and load-balancer health probes.
        """
        return jsonify({"status": "ok", "phase": 3}), 200

    # ------------------------------------------------------------------
    # Global error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "HTTP method not allowed on this endpoint."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error."}), 500

    return app


# ----------------------------------------------------------------------
# Dev-server entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application = create_app()

    print(f"[TradePost] Phase 3 server starting on http://127.0.0.1:{port}")
    print(f"[TradePost] Debug mode: {application.config['DEBUG']}")
    print("[TradePost] Endpoints:")
    print("  GET  /health")
    print("  POST /auth/register")
    print("  POST /auth/login")
    print("  GET  /api/posts")
    print("  POST /api/posts")
    print("  GET  /api/posts/<post_id>")
    print("  GET  /api/posts/<post_id>/offers")
    print("  POST /api/offers")
    print("  PUT  /api/offers/<offer_id>/counter")
    print("  PUT  /api/offers/<offer_id>/accept")
    print("  PUT  /api/offers/<offer_id>/decline")

    application.run(host="0.0.0.0", port=port)
