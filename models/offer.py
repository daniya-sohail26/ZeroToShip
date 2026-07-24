class NegotiationOffer:
    """
    Represents an offer on a TradePost.
    """
    def __init__(self, offer_id: int, post_id: int, proposer_id: int, offered_item_details: str, turn_holder_id: int):
        self.offer_id = offer_id
        self.post_id = post_id
        self.proposer_id = proposer_id
        self.offered_item_details = offered_item_details
        self.turn_holder_id = turn_holder_id

    def to_dict(self):
        """Serializes the object into a standard Python dictionary."""
        return {
            "offer_id": self.offer_id,
            "post_id": self.post_id,
            "proposer_id": self.proposer_id,
            "offered_item_details": self.offered_item_details,
            "turn_holder_id": self.turn_holder_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a dictionary into a NegotiationOffer object."""
        return cls(
            offer_id=data.get("offer_id"),
            post_id=data.get("post_id"),
            proposer_id=data.get("proposer_id"),
            offered_item_details=data.get("offered_item_details"),
            turn_holder_id=data.get("turn_holder_id")
        )
