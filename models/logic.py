"""
models/logic.py
===============
TradeStore — the central persistence and business-logic engine for Phase 3.

Extends Phase 1's SerializationEngine pattern with full CRUD support for
TradePost and NegotiationOffer objects, plus the two core transactional
state validators:

    1. Turn-Taking  — every counter-offer programmatically flips turn_holder_id
                      so only the correct party can move next.

    2. Auto-Decline — accepting an offer instantly scans the entire offers
                      array and declines every rival offer that targets the
                      same post_id, preventing double-acceptance.

Data is stored in a single flat JSON file (tradepost_db.json) whose schema
mirrors Phase 1's SerializationEngine output so the two phases stay
interoperable.

Schema
------
{
    "posts":  [ { post fields ... }, ... ],
    "offers": [ { offer fields ... }, ... ]
}

Post status values : "Open" | "Closed"
Offer status values: "Pending" | "Accepted" | "Declined" | "Countered"
"""

import json
import os

# ---------------------------------------------------------------------------
# Inline model definitions
# (Phase 1 models are in a sibling repo; we keep Phase 2/3 self-contained
#  by re-declaring lightweight versions that are wire-compatible.)
# ---------------------------------------------------------------------------

class TradePost:
    VALID_STATUSES = {"Open", "Closed"}

    def __init__(self, post_id: int, title: str, description: str,
                 owner_id: int, status: str = "Open"):
        self.post_id     = post_id
        self.title       = title
        self.description = description
        self.owner_id    = owner_id
        self.status      = status

    def to_dict(self) -> dict:
        return {
            "post_id":     self.post_id,
            "title":       self.title,
            "description": self.description,
            "owner_id":    self.owner_id,
            "status":      self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TradePost":
        return cls(
            post_id=d["post_id"],
            title=d["title"],
            description=d["description"],
            owner_id=d["owner_id"],
            status=d.get("status", "Open"),
        )


class NegotiationOffer:
    VALID_STATUSES = {"Pending", "Accepted", "Declined", "Countered"}

    def __init__(self, offer_id: int, post_id: int, proposer_id: int,
                 offered_item_details: str, turn_holder_id: int,
                 status: str = "Pending"):
        self.offer_id            = offer_id
        self.post_id             = post_id
        self.proposer_id         = proposer_id
        self.offered_item_details = offered_item_details
        self.turn_holder_id      = turn_holder_id   # whose move it is
        self.status              = status

    def to_dict(self) -> dict:
        return {
            "offer_id":             self.offer_id,
            "post_id":              self.post_id,
            "proposer_id":          self.proposer_id,
            "offered_item_details": self.offered_item_details,
            "turn_holder_id":       self.turn_holder_id,
            "status":               self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NegotiationOffer":
        return cls(
            offer_id=d["offer_id"],
            post_id=d["post_id"],
            proposer_id=d["proposer_id"],
            offered_item_details=d["offered_item_details"],
            turn_holder_id=d["turn_holder_id"],
            status=d.get("status", "Pending"),
        )


# ---------------------------------------------------------------------------
# TradeStore — persistence + business rules
# ---------------------------------------------------------------------------

DB_FILE = "tradepost_db.json"


class TradeStore:
    """
    Single source of truth for all posts and offers.

    Every public method loads the current state from disk, applies the
    requested mutation, and immediately flushes back to disk — keeping
    the flat-file consistent even across multiple requests.
    """

    def __init__(self, filepath: str = DB_FILE):
        self.filepath = filepath

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def _load(self) -> tuple[list[TradePost], list[NegotiationOffer]]:
        if not os.path.exists(self.filepath):
            return [], []
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return [], []
        posts  = [TradePost.from_dict(p)        for p in data.get("posts",  [])]
        offers = [NegotiationOffer.from_dict(o) for o in data.get("offers", [])]
        return posts, offers

    def _save(self, posts: list[TradePost],
              offers: list[NegotiationOffer]) -> None:
        data = {
            "posts":  [p.to_dict() for p in posts],
            "offers": [o.to_dict() for o in offers],
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ------------------------------------------------------------------
    # Auto-increment helpers
    # ------------------------------------------------------------------

    def _next_post_id(self, posts: list[TradePost]) -> int:
        return max((p.post_id for p in posts), default=0) + 1

    def _next_offer_id(self, offers: list[NegotiationOffer]) -> int:
        return max((o.offer_id for o in offers), default=0) + 1

    # ------------------------------------------------------------------
    # Post operations
    # ------------------------------------------------------------------

    def get_all_posts(self, status_filter: str | None = None) -> list[TradePost]:
        """
        Return all posts, optionally filtered by status.
        Pass status_filter="Open" to show only live listings.
        """
        posts, _ = self._load()
        if status_filter:
            posts = [p for p in posts if p.status == status_filter]
        return posts

    def get_post(self, post_id: int) -> TradePost | None:
        posts, _ = self._load()
        for p in posts:
            if p.post_id == post_id:
                return p
        return None

    def create_post(self, title: str, description: str,
                    owner_id: int) -> TradePost:
        """Create and persist a new TradePost with status='Open'."""
        posts, offers = self._load()
        post = TradePost(
            post_id=self._next_post_id(posts),
            title=title,
            description=description,
            owner_id=owner_id,
        )
        posts.append(post)
        self._save(posts, offers)
        return post

    # ------------------------------------------------------------------
    # Offer operations
    # ------------------------------------------------------------------

    def get_offers_for_post(self, post_id: int) -> list[NegotiationOffer]:
        """Return all offers targeting a specific post."""
        _, offers = self._load()
        return [o for o in offers if o.post_id == post_id]

    def get_offer(self, offer_id: int) -> NegotiationOffer | None:
        _, offers = self._load()
        for o in offers:
            if o.offer_id == offer_id:
                return o
        return None

    def create_offer(self, post_id: int, proposer_id: int,
                     offered_item_details: str) -> tuple[NegotiationOffer, str | None]:
        """
        Submit a new offer on an open post.

        Business rules enforced
        -----------------------
        * The post must exist and be 'Open'.
        * The post owner cannot bid on their own listing.
        * A proposer may only have one active (Pending/Countered) offer per post.

        Turn initialisation
        -------------------
        turn_holder_id is set to the post owner so they receive the first
        decision — accept, decline, or counter.

        Returns
        -------
        (offer, error_message)   — error_message is None on success.
        """
        posts, offers = self._load()

        # --- validate post ---
        post = next((p for p in posts if p.post_id == post_id), None)
        if post is None:
            return None, "Post not found."
        if post.status != "Open":
            return None, "This post is no longer accepting offers."
        if post.owner_id == proposer_id:
            return None, "You cannot place an offer on your own post."

        # --- one active offer per proposer per post ---
        active = [o for o in offers
                  if o.post_id == post_id
                  and o.proposer_id == proposer_id
                  and o.status in ("Pending", "Countered")]
        if active:
            return None, "You already have an active offer on this post."

        offer = NegotiationOffer(
            offer_id=self._next_offer_id(offers),
            post_id=post_id,
            proposer_id=proposer_id,
            offered_item_details=offered_item_details,
            turn_holder_id=post.owner_id,   # owner moves first
            status="Pending",
        )
        offers.append(offer)
        self._save(posts, offers)
        return offer, None

    # ------------------------------------------------------------------
    # Turn-Taking validator
    # ------------------------------------------------------------------

    def counter_offer(self, offer_id: int, acting_user_id: int,
                      new_item_details: str) -> tuple[NegotiationOffer | None, str | None]:
        """
        Submit a counter-offer, flipping turn_holder_id to the other party.

        Business rules enforced
        -----------------------
        * Offer must exist and be in 'Pending' or 'Countered' state.
        * Only the current turn_holder may counter.
        * The underlying post must still be 'Open'.

        Turn-flip logic
        ---------------
        The two parties involved are: post.owner_id and offer.proposer_id.
        After a counter, the turn flips to whichever party did NOT just move.

        Returns
        -------
        (updated_offer, error_message)
        """
        posts, offers = self._load()

        offer = next((o for o in offers if o.offer_id == offer_id), None)
        if offer is None:
            return None, "Offer not found."

        if offer.status not in ("Pending", "Countered"):
            return None, f"Cannot counter an offer with status '{offer.status}'."

        if offer.turn_holder_id != acting_user_id:
            return None, "It is not your turn to counter this offer."

        post = next((p for p in posts if p.post_id == offer.post_id), None)
        if post is None or post.status != "Open":
            return None, "The associated post is no longer open."

        # --- flip the turn ---
        other_party = (
            offer.proposer_id
            if acting_user_id == post.owner_id
            else post.owner_id
        )

        offer.offered_item_details = new_item_details
        offer.turn_holder_id       = other_party
        offer.status               = "Countered"

        self._save(posts, offers)
        return offer, None

    # ------------------------------------------------------------------
    # Accept + Auto-Decline engine
    # ------------------------------------------------------------------

    def accept_offer(self, offer_id: int,
                     acting_user_id: int) -> tuple[NegotiationOffer | None, str | None]:
        """
        Accept an offer and auto-decline every rival offer on the same post.

        Business rules enforced
        -----------------------
        * Offer must exist and be 'Pending' or 'Countered'.
        * Only the current turn_holder may accept.
        * Post must be 'Open'.

        Auto-Decline cascade
        --------------------
        Once the target offer is marked 'Accepted':
          1. The parent post status is set to 'Closed'.
          2. Every other offer whose post_id matches is set to 'Declined'
             in a single pass over the offers array — no further requests
             needed.

        Returns
        -------
        (accepted_offer, error_message)
        """
        posts, offers = self._load()

        offer = next((o for o in offers if o.offer_id == offer_id), None)
        if offer is None:
            return None, "Offer not found."

        if offer.status not in ("Pending", "Countered"):
            return None, f"Cannot accept an offer with status '{offer.status}'."

        if offer.turn_holder_id != acting_user_id:
            return None, "It is not your turn to accept this offer."

        post = next((p for p in posts if p.post_id == offer.post_id), None)
        if post is None or post.status != "Open":
            return None, "The associated post is no longer open."

        # --- accept the target offer ---
        offer.status = "Accepted"

        # --- close the post ---
        post.status = "Closed"

        # --- auto-decline all rivals targeting the same post ---
        for o in offers:
            if (o.post_id  == offer.post_id
                    and o.offer_id != offer_id
                    and o.status in ("Pending", "Countered")):
                o.status = "Declined"

        self._save(posts, offers)
        return offer, None

    # ------------------------------------------------------------------
    # Manual decline
    # ------------------------------------------------------------------

    def decline_offer(self, offer_id: int,
                      acting_user_id: int) -> tuple[NegotiationOffer | None, str | None]:
        """
        Manually decline an offer.

        Only the current turn_holder (i.e. the party whose move it is)
        can decline.  The post remains 'Open' so other offers can proceed.

        Returns
        -------
        (declined_offer, error_message)
        """
        posts, offers = self._load()

        offer = next((o for o in offers if o.offer_id == offer_id), None)
        if offer is None:
            return None, "Offer not found."

        if offer.status not in ("Pending", "Countered"):
            return None, f"Cannot decline an offer with status '{offer.status}'."

        if offer.turn_holder_id != acting_user_id:
            return None, "It is not your turn to decline this offer."

        offer.status = "Declined"
        self._save(posts, offers)
        return offer, None
