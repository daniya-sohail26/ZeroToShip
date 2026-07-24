# TradePost — Phase 1

A lightweight, web-based peer-to-peer barter exchange backend. Phase 1 focuses on defining the core data models and a flat-file serialization engine.

## Project Structure

```
ZeroToShip/Phase 1/
├── models/
│   ├── __init__.py          # Empty init for Python package
│   ├── post.py              # TradePost model
│   └── offer.py             # NegotiationOffer model
├── engine.py                # Serialization/deserialization engine
├── .gitignore               # Ignores __pycache__/ and tradepost_db.json
└── README.md                # This file
```

## Technical Implementation

### TradePost Model (`models/post.py`)

Represents a barter listing posted by a user. Attributes:

| Attribute    | Type | Description |
|-------------|------|-------------|
| `post_id`   | int  | Unique identifier for the post |
| `title`     | str  | Name of the item being offered |
| `description` | str | Details about the item |
| `owner_id`  | int  | User ID of the person who created the post |
| `status`    | str  | Either `"Open"` (accepting offers) or `"Traded"` (listing closed) |

**Methods:**
- `to_dict()` — Serialises the object into a plain Python dictionary for JSON output.
- `from_dict(cls, data)` — Class method that reconstructs a `TradePost` from a dictionary; defaults `status` to `"Open"` if missing.

### NegotiationOffer Model (`models/offer.py`)

Represents an offer made by a user on a specific TradePost. Attributes:

| Attribute             | Type | Description |
|----------------------|------|-------------|
| `offer_id`           | int  | Unique identifier for the offer |
| `post_id`            | int  | Foreign key referencing the parent TradePost |
| `proposer_id`        | int  | User ID of the person making the offer |
| `offered_item_details` | str | Text description of what the proposer offers in exchange |
| `turn_holder_id`     | int  | User ID of the person whose turn it is to respond (enables turn-based negotiation) |

**Methods:**
- `to_dict()` — Serialises the object into a dictionary.
- `from_dict(cls, data)` — Class method that reconstructs a `NegotiationOffer` from a dictionary.

### Serialization Engine (`engine.py`)

The `SerializationEngine` class manages reading and writing model data to a JSON flat-file (`tradepost_db.json`).

- **`save_data(posts, offers)`** — Accepts lists of `TradePost` and `NegotiationOffer` objects, calls `.to_dict()` on each, wraps them in a structured `{"posts": [...], "offers": [...]}` dictionary, and writes the result as pretty-printed JSON.
- **`load_data(filepath)`** — Reads the JSON file, calls `TradePost.from_dict()` and `NegotiationOffer.from_dict()` on each entry to reconstruct the object lists. Returns `{"posts": [...], "offers": [...]}`. Handles missing or corrupt files gracefully by returning empty lists.

### Design Decisions

- **No external database** — Uses a flat JSON file for persistence, keeping the project self-contained and easy to debug.
- **`to_dict()` / `from_dict()` pattern** — Decouples in-memory representation from storage format, making it trivial to swap the backend to a real database later.
- **`turn_holder_id` on offers** — Pre-architects the turn-based negotiation flow planned for later phases.
- **Graceful degradation** — `load_data()` returns empty lists if the file is missing or corrupted, preventing crashes on first run.

## How to Run

```python
from models.post import TradePost
from models.offer import NegotiationOffer
from engine import SerializationEngine

# Create sample data
post = TradePost(post_id=1, title="Vintage Guitar", description="1965 Fender Stratocaster", owner_id=1)
offer = NegotiationOffer(offer_id=1, post_id=1, proposer_id=2, offered_item_details="Mountain bike", turn_holder_id=1)

# Save to flat-file
SerializationEngine.save_data(posts=[post], offers=[offer])

# Load from flat-file
data = SerializationEngine.load_data()
print(data["posts"][0].title)  # "Vintage Guitar"
```

## Future Phases

- **Phase 2:** Flask/FastAPI server with RESTful routes
- **Phase 3:** Turn-based negotiation state machine and cascade auto-decline logic
- **Phase 4:** Frontend templates with session cookies and form handling
- **Phase 5:** Full integration and testing