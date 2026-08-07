"""
views/routes.py
===============
Trading API Blueprint — all RESTful endpoints for listings and negotiations.

Every route (except GET /api/posts) requires a valid JWT via @token_required.
The authenticated user is injected as `current_user` by the gatekeeper.

Endpoints
---------
    GET  /api/posts                      List all open listings
    POST /api/posts                      Create a new listing          [auth]
    GET  /api/posts/<post_id>            Get a single post             [auth]
    GET  /api/posts/<post_id>/offers     Get all offers on a post      [auth]
    POST /api/offers                     Submit an initial offer       [auth]
    PUT  /api/offers/<offer_id>/counter  Counter an offer (turn-flip)  [auth]
    PUT  /api/offers/<offer_id>/accept   Accept + auto-decline rivals  [auth]
    PUT  /api/offers/<offer_id>/decline  Manually decline an offer     [auth]
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from middleware.auth_guard import token_required
from models.logic import TradeStore

api_bp = Blueprint("api", __name__, url_prefix="/api")
_store = TradeStore()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _post_response(post) -> dict:
    return post.to_dict()

def _offer_response(offer) -> dict:
    return offer.to_dict()


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

@api_bp.route("/posts", methods=["GET"])
def get_posts():
    """
    GET /api/posts

    Returns all posts. Accepts an optional ?status= query param to filter.
    No authentication required — public browsing is allowed.

    Query params:
        status  (optional)  "Open" | "Closed"

    Response 200:
        { "posts": [ { post }, ... ], "count": N }
    """
    status_filter = request.args.get("status")
    posts = _store.get_all_posts(status_filter=status_filter)
    return jsonify({
        "posts": [_post_response(p) for p in posts],
        "count": len(posts),
    }), 200


@api_bp.route("/posts", methods=["POST"])
@token_required
def create_post(current_user):
    """
    POST /api/posts                                             [auth required]

    Create a new trade listing owned by the authenticated user.

    Request body (JSON):
        {
            "title":       "Vintage guitar",
            "description": "1972 Fender Telecaster, great condition"
        }

    Response 201:
        { "message": "...", "post": { post } }

    Response 400:
        missing / empty title or description
    """
    body = request.get_json(silent=True) or {}
    title       = (body.get("title")       or "").strip()
    description = (body.get("description") or "").strip()
    image_url   = body.get("image_url")  # optional, set after /api/upload

    if not title or not description:
        return jsonify({"error": "Both 'title' and 'description' are required."}), 400

    post = _store.create_post(
        title=title,
        description=description,
        owner_id=current_user.user_id,
        image_url=image_url,
    )
    return jsonify({
        "message": "Post created successfully.",
        "post":    _post_response(post),
    }), 201


# ---------------------------------------------------------------------------
# Image Upload
# ---------------------------------------------------------------------------

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")


@api_bp.route("/upload", methods=["POST"])
@token_required
def upload_image(current_user):
    """
    POST /api/upload                                            [auth required]

    Upload a listing image. Expects multipart/form-data with field 'image'.
    Saves to static/uploads/ and returns the relative URL.

    Response 201: { "image_url": "uploads/uuid.ext" }
    """
    if "image" not in request.files:
        return jsonify({"error": "No file provided. Send a multipart field named 'image'."}), 400

    f = request.files["image"]
    if not f or f.filename == "":
        return jsonify({"error": "No file selected."}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Unsupported format '{ext}'. Use PNG, JPG, GIF, or WEBP."}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_DIR, filename))

    return jsonify({"image_url": f"uploads/{filename}"}), 201


@api_bp.route("/posts/<int:post_id>", methods=["GET"])
@token_required
def get_post(current_user, post_id):
    """
    GET /api/posts/<post_id>                                    [auth required]

    Retrieve a single post by ID.

    Response 200: { "post": { post } }
    Response 404: post not found
    """
    post = _store.get_post(post_id)
    if post is None:
        return jsonify({"error": f"Post {post_id} not found."}), 404
    return jsonify({"post": _post_response(post)}), 200


@api_bp.route("/posts/<int:post_id>/offers", methods=["GET"])
@token_required
def get_post_offers(current_user, post_id):
    """
    GET /api/posts/<post_id>/offers                             [auth required]

    Retrieve all offers submitted on a specific post.
    Only the post owner or an involved proposer should call this in practice,
    but the route itself just requires a valid session.

    Response 200: { "offers": [ { offer }, ... ], "count": N }
    Response 404: post not found
    """
    post = _store.get_post(post_id)
    if post is None:
        return jsonify({"error": f"Post {post_id} not found."}), 404

    offers = _store.get_offers_for_post(post_id)
    return jsonify({
        "offers": [_offer_response(o) for o in offers],
        "count":  len(offers),
    }), 200


# ---------------------------------------------------------------------------
# Offer submission
# ---------------------------------------------------------------------------

@api_bp.route("/offers", methods=["POST"])
@token_required
def create_offer(current_user):
    """
    POST /api/offers                                            [auth required]

    Submit an initial barter offer on an open listing.
    turn_holder_id is automatically set to the post owner.

    Request body (JSON):
        {
            "post_id":              1,
            "offered_item_details": "Roland TR-808 drum machine, mint"
        }

    Response 201:
        { "message": "...", "offer": { offer } }

    Response 400 / 404:
        business rule violation (see TradeStore.create_offer docstring)
    """
    body = request.get_json(silent=True) or {}
    post_id              = body.get("post_id")
    offered_item_details = (body.get("offered_item_details") or "").strip()

    if post_id is None or not offered_item_details:
        return jsonify({"error": "Both 'post_id' and 'offered_item_details' are required."}), 400

    if not isinstance(post_id, int):
        return jsonify({"error": "'post_id' must be an integer."}), 400

    offer, error = _store.create_offer(
        post_id=post_id,
        proposer_id=current_user.user_id,
        offered_item_details=offered_item_details,
    )
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Offer submitted. Awaiting response from the post owner.",
        "offer":   _offer_response(offer),
    }), 201


# ---------------------------------------------------------------------------
# Turn-Taking: counter-offer
# ---------------------------------------------------------------------------

@api_bp.route("/offers/<int:offer_id>/counter", methods=["PUT"])
@token_required
def counter_offer(current_user, offer_id):
    """
    PUT /api/offers/<offer_id>/counter                          [auth required]

    Submit a counter-offer.  Programmatically flips turn_holder_id to the
    other party so they must respond next.

    Business rules (enforced in TradeStore.counter_offer):
        - Offer must be Pending or Countered.
        - Caller must be the current turn_holder.
        - The parent post must still be Open.

    Request body (JSON):
        {
            "offered_item_details": "I'll add a Korg Minilogue too"
        }

    Response 200:
        { "message": "...", "offer": { offer } }   (turn_holder_id is now the other party)

    Response 400 / 403:
        business rule violation
    """
    body = request.get_json(silent=True) or {}
    new_details = (body.get("offered_item_details") or "").strip()

    if not new_details:
        return jsonify({"error": "'offered_item_details' is required for a counter-offer."}), 400

    offer, error = _store.counter_offer(
        offer_id=offer_id,
        acting_user_id=current_user.user_id,
        new_item_details=new_details,
    )
    if error:
        status_code = 403 if "not your turn" in error.lower() else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Counter-offer submitted. Turn passed to the other party.",
        "offer":   _offer_response(offer),
    }), 200


# ---------------------------------------------------------------------------
# Accept + Auto-Decline cascade
# ---------------------------------------------------------------------------

@api_bp.route("/offers/<int:offer_id>/accept", methods=["PUT"])
@token_required
def accept_offer(current_user, offer_id):
    """
    PUT /api/offers/<offer_id>/accept                           [auth required]

    Accept a specific offer.

    Auto-Decline cascade (enforced in TradeStore.accept_offer):
        - The accepted offer status → "Accepted".
        - The parent post status   → "Closed".
        - Every other Pending/Countered offer on the same post_id is
          instantly set to "Declined" in a single JSON array scan.

    Business rules:
        - Offer must be Pending or Countered.
        - Caller must be the current turn_holder.
        - Post must be Open.

    Response 200:
        {
            "message":          "...",
            "accepted_offer":   { offer },
            "auto_declined":    N          (number of rival offers declined)
        }
    """
    # load offers BEFORE the accept so we can report how many were declined
    offers_before = _store.get_offers_for_post(
        (_store.get_offer(offer_id) or type("", (), {"post_id": -1})()).post_id
    )
    rival_count = len([
        o for o in offers_before
        if o.offer_id != offer_id and o.status in ("Pending", "Countered")
    ])

    offer, error = _store.accept_offer(
        offer_id=offer_id,
        acting_user_id=current_user.user_id,
    )
    if error:
        status_code = 403 if "not your turn" in error.lower() else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message":        "Offer accepted. The trade is complete.",
        "accepted_offer": _offer_response(offer),
        "auto_declined":  rival_count,
    }), 200


# ---------------------------------------------------------------------------
# Manual decline
# ---------------------------------------------------------------------------

@api_bp.route("/offers/<int:offer_id>/decline", methods=["PUT"])
@token_required
def decline_offer(current_user, offer_id):
    """
    PUT /api/offers/<offer_id>/decline                          [auth required]

    Manually decline an offer.  The post stays Open so other offers can
    continue.  Only the current turn_holder may decline.

    Response 200:
        { "message": "...", "offer": { offer } }
    """
    offer, error = _store.decline_offer(
        offer_id=offer_id,
        acting_user_id=current_user.user_id,
    )
    if error:
        status_code = 403 if "not your turn" in error.lower() else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Offer declined.",
        "offer":   _offer_response(offer),
    }), 200
