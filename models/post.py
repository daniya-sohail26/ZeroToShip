class TradePost:
    """
    Represents a post for a barter exchange.
    """
    def __init__(self, post_id: int, title: str, description: str, owner_id: int, status: str = "Open"):
        self.post_id = post_id
        self.title = title
        self.description = description
        self.owner_id = owner_id
        self.status = status

    def to_dict(self):
        """Serializes the object into a standard Python dictionary."""
        return {
            "post_id": self.post_id,
            "title": self.title,
            "description": self.description,
            "owner_id": self.owner_id,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a dictionary into a TradePost object."""
        return cls(
            post_id=data.get("post_id"),
            title=data.get("title"),
            description=data.get("description"),
            owner_id=data.get("owner_id"),
            status=data.get("status", "Open")
        )
