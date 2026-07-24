import json
import os
from models.post import TradePost
from models.offer import NegotiationOffer

DB_FILE = "tradepost_db.json"

class SerializationEngine:
    """
    Handles serialization of Python objects directly to a JSON flat-file.
    """
    @staticmethod
    def save_data(posts, offers, filepath=DB_FILE):
        data = {
            "posts": [post.to_dict() for post in posts],
            "offers": [offer.to_dict() for offer in offers]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_data(filepath=DB_FILE):
        if not os.path.exists(filepath):
            return {"posts": [], "offers": []}
            
        with open(filepath, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {"posts": [], "offers": []}
                
        posts = [TradePost.from_dict(p) for p in data.get("posts", [])]
        offers = [NegotiationOffer.from_dict(o) for o in data.get("offers", [])]
        
        return {"posts": posts, "offers": offers}
