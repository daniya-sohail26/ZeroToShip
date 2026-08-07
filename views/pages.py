"""
views/pages.py
==============
Flask page routes — serve Jinja2 HTML templates populated with live data
from TradeStore and UserStore.

Routes
------
    GET  /               → marketplace (all open posts, live from tradepost_db.json)
    GET  /dashboard      → negotiation dashboard (live offers for current user)
    GET  /login          → login page
    GET  /register       → register page
    GET  /post/<id>      → single post detail with its live offer list

All dashboard/post-detail routes decode the JWT from a cookie called `tp_token`
(set by the browser JS after login) to identify the current user without
requiring every HTML link to carry an Authorization header.
"""

import jwt
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, current_app, make_response
)
from models.logic  import TradeStore
from models.user   import UserStore

pages_bp   = Blueprint("pages", __name__)
_trade     = TradeStore()
_users     = UserStore()


# ── helpers ───────────────────────────────────────────────────────────────────

def _current_user_from_cookie():
    """
    Decode the JWT stored in the tp_token cookie.
    Returns a User object or None when unauthenticated / token invalid.
    """
    token = request.cookies.get("tp_token", "")
    if not token:
        return None
    try:
        secret  = current_app.config["JWT_SECRET"]
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return _users.find_by_id(int(payload["sub"]))
    except Exception:
        return None


def _require_login():
    """Redirect to /login when the visitor is not authenticated."""
    return redirect(url_for("pages.login_page"))


# ── pages ─────────────────────────────────────────────────────────────────────

@pages_bp.route("/")
def marketplace():
    """
    Landing page — Trading Board.
    Loads ALL posts from tradepost_db.json and passes them to the template.
    """
    user  = _current_user_from_cookie()
    posts = _trade.get_all_posts()          # all statuses; template filters client-side

    # counts for the header badges
    open_count   = sum(1 for p in posts if p.status == "Open")
    closed_count = sum(1 for p in posts if p.status == "Closed")

    # per-post offer count so the cards can display it
    all_offers = _trade.get_all_offers()
    offer_counts = {}
    for o in all_offers:
        offer_counts[o.post_id] = offer_counts.get(o.post_id, 0) + 1

    active_offer_posts = sum(1 for count in offer_counts.values() if count > 0)
    total_offers = len(all_offers)

    return render_template(
        "index.html",
        user         = user,
        posts        = posts,
        offer_counts = offer_counts,
        active_offer_posts = active_offer_posts,
        total_offers = total_offers,
        open_count   = open_count,
        closed_count = closed_count,
    )


@pages_bp.route("/dashboard")
def dashboard():
    """
    Negotiation Dashboard — shows live offers involving the current user,
    both as post owner and as proposer.
    Redirects to /login when unauthenticated.
    """
    user = _current_user_from_cookie()
    if user is None:
        return _require_login()

    posts       = _trade.get_all_posts()
    all_offers  = _trade.get_all_offers()
    post_map    = {p.post_id: p for p in posts}

    # collect offers where this user is either the post owner or the proposer
    my_offers = []
    for o in all_offers:
        post = post_map.get(o.post_id)
        if post and (o.proposer_id == user.user_id or post.owner_id == user.user_id):
            # determine turn state from user's perspective
            if o.status in ("Accepted", "Declined"):
                state = o.status.lower()
            elif o.turn_holder_id == user.user_id:
                state = "your-turn"
            else:
                state = "waiting"

            # resolve peer username
            peer_id = post.owner_id if o.proposer_id == user.user_id else o.proposer_id
            peer    = _users.find_by_id(peer_id)

            my_offers.append({
                "offer":      o,
                "post":       post,
                "state":      state,
                "peer":       peer.username if peer else f"user#{peer_id}",
                "is_my_turn": o.turn_holder_id == user.user_id,
            })

    # sidebar stats
    need_action = sum(1 for x in my_offers if x["state"] == "your-turn")
    waiting     = sum(1 for x in my_offers if x["state"] == "waiting")
    completed   = sum(1 for x in my_offers if x["state"] in ("accepted", "declined"))

    return render_template(
        "dashboard.html",
        user        = user,
        my_offers   = my_offers,
        need_action = need_action,
        waiting     = waiting,
        completed   = completed,
        total       = len(my_offers),
    )


@pages_bp.route("/post/<int:post_id>")
def post_detail(post_id):
    """Single post detail with its offer list."""
    user   = _current_user_from_cookie()
    post   = _trade.get_post(post_id)
    if post is None:
        return render_template("404.html"), 404

    offers      = _trade.get_offers_for_post(post_id)
    all_offers  = _trade.get_all_offers()
    offer_counts = {}
    for o in all_offers:
        offer_counts[o.post_id] = offer_counts.get(o.post_id, 0) + 1

    return render_template(
        "post_detail.html",
        user         = user,
        post         = post,
        offers       = offers,
        offer_counts = offer_counts,
    )


@pages_bp.route("/login")
def login_page():
    user = _current_user_from_cookie()
    if user:
        return redirect(url_for("pages.marketplace"))
    return render_template("login.html")


@pages_bp.route("/register")
def register_page():
    user = _current_user_from_cookie()
    if user:
        return redirect(url_for("pages.marketplace"))
    return render_template("register.html")


@pages_bp.route("/logout")
def logout():
    """Clear the JWT cookie and redirect to login."""
    resp = make_response(redirect(url_for("pages.login_page")))
    resp.delete_cookie("tp_token")
    return resp
