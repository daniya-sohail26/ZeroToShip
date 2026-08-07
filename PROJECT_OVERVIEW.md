# TradePost — Project Overview

> **ZeroToShip Submission · Phase 5 Final**

---

## 📌 Project Information

### Project Description

**TradePost** is a peer-to-peer barter exchange platform that lets users list items they own, browse listings from others, and negotiate trades through a structured turn-based counter-offer system — all without any money changing hands.

In the real world, many people hold onto items they no longer need while simultaneously wanting things they cannot easily afford. Traditional marketplaces require monetary transactions, creating a barrier for individuals who want to trade value for value. TradePost solves this by providing a structured, negotiation-first digital marketplace where the medium of exchange is *items*, not currency.

---

### Pain Point

The core pain point is the **friction of peer-to-peer barter in the digital age**:

- Informal trades (Facebook Marketplace, WhatsApp groups) lack any negotiation structure — users post, someone replies "interested", and the conversation dies.
- There is no system to track the state of a negotiation, prevent double-acceptance, or ensure both parties know whose "turn" it is.
- Without a turn-based protocol, deals collapse at the negotiation phase even when both parties genuinely want to trade.
- Post owners have no way to simultaneously evaluate multiple offers fairly.

---

### Proposed Solution

TradePost provides a **full-stack barter marketplace** with two core algorithmic innovations:

**1. Turn-Taking Protocol**
Every negotiation has a `turn_holder_id`. The initial offer sets the post owner as the first turn-holder. Each counter-offer programmatically flips the turn to the other party. Only the current turn-holder can accept, decline, or counter — preventing race conditions and confusion about who should act next.

**2. Auto-Decline Cascade**
When a trade is accepted, the platform performs a single-pass scan of all offers targeting the same post and instantly declines every rival `Pending` or `Countered` offer. The post status is atomically set to `Closed`. This prevents double-acceptance and ensures every other bidder receives an immediate, respectful response.

**System Architecture:**
```
Browser (Jinja2 + Vanilla JS)
        │ fetch() API calls (JWT Bearer)
        ▼
Flask Application (app.py factory)
    ├── views/auth.py      → POST /auth/register, /auth/login
    ├── views/routes.py    → REST API /api/posts, /api/offers
    ├── views/pages.py     → HTML page routes (/, /dashboard, /post/<id>)
    └── middleware/auth_guard.py → @token_required JWT decorator
        │
        ▼
    models/logic.py (TradeStore)   → tradepost_db.json
    models/user.py  (UserStore)    → users_db.json
```

Sessions are JWT-based: the token is stored in `localStorage` and also set as a `tp_token` cookie so Flask page routes can authenticate server-side without requiring every link to carry an Authorization header.

---

### Target Users

| User Type | Benefit |
|---|---|
| **Individuals** with unused items | Post listings and receive structured barter offers instead of money |
| **Budget-conscious consumers** | Acquire items through fair trade without spending cash |
| **Collectors & hobbyists** | Negotiate item-for-item swaps with clear turn-based protocol |
| **Students & early-career** | Access items through trade when cash is limited |

The platform is especially valuable for electronics, instruments, books, sports equipment, collectibles, and any category where two parties are likely to have complementary wants.

---

## 💻 Development Details & Deliverables

### Technologies Used

| Layer | Technology | Version |
|---|---|---|
| **Backend Language** | Python | 3.12 |
| **Web Framework** | Flask | 3.1.1 |
| **Authentication** | PyJWT (HS256, 24-hour tokens) | 2.10.1 |
| **Persistence** | Flat-file JSON (`tradepost_db.json`, `users_db.json`) | — |
| **Templating** | Jinja2 (via Flask) | Built-in |
| **Frontend Styling** | Vanilla CSS (custom design system, glassmorphism, CSS Grid, CSS custom properties) | — |
| **Frontend Logic** | Vanilla JavaScript (ES2020+, Fetch API, IntersectionObserver, Canvas API) | — |
| **Password Security** | SHA-256 with random 32-char hex salt | Built-in |

### External Libraries / Frameworks Used

| Library | Purpose |
|---|---|
| **Flask 3.1** | WSGI web framework — routing, Jinja2 templating, Blueprints |
| **PyJWT 2.10** | JWT encode/decode for stateless auth sessions |
| **Google Fonts (Inter, Outfit, JetBrains Mono)** | Premium typography via CDN |
| **Canvas API** (built-in browser) | Animated particle network background |
| **IntersectionObserver API** (built-in browser) | Scroll-reveal entrance animations |

> No React, Vue, Tailwind, Bootstrap, or any other third-party CSS/JS framework is used. The entire frontend — including the glassmorphism design system, animations, and interactive components — is hand-crafted in vanilla CSS and JavaScript.

### GitHub Repository Link

```
https://github.com/daniya-sohail26/ZeroToShip
```

> The repository is public and contains the complete project under `Phase 2/`.


## 📝 Reflection & Future Scope

### Biggest Challenge Faced

The most difficult part was implementing the **turn-taking and auto-decline cascade correctly and atomically**.

The challenge was not just the business logic itself, but ensuring it was **race-condition-safe** in a stateless flat-file environment. Because Flask serves multiple concurrent requests and the persistence layer is a single JSON file, there was a real risk of two users simultaneously reading stale state, both computing valid moves, and corrupting the negotiation record.

The solution was to enforce a **load → mutate → save** cycle inside every `TradeStore` method, with the `turn_holder_id` check acting as the atomic gate. A user can only advance the negotiation if they are the current turn-holder at the moment of the write — making incorrect concurrent moves self-correcting (one will succeed, the other will receive a 403 "not your turn" error).

The auto-decline cascade was specifically tricky: it needed to run inside the same `_save()` call as the accept, so the database never exists in a state where an offer is accepted but rivals are still pending — even for a millisecond.

---

### How Modular Development Helped

Breaking TradePost into modules made development dramatically more efficient and maintainable:

| Module | Responsibility | Independence |
|---|---|---|
| `models/logic.py` | Business rules + persistence | Fully testable without Flask |
| `models/user.py` | User auth + salted hashing | No dependency on trade logic |
| `views/auth.py` | JWT issue endpoints | No dependency on trade logic |
| `views/routes.py` | REST API | No dependency on HTML/CSS |
| `views/pages.py` | HTML page rendering | No dependency on REST API |
| `middleware/auth_guard.py` | JWT validation decorator | Reusable across any blueprint |
| `static/css/style.css` | Design system | Completely decoupled from logic |
| `static/js/app.js` | UI interactions + animations | Decoupled from backend |

This separation meant:
- The business logic (`TradeStore`) could be verified independently before wiring to Flask
- The auth middleware was written once and applied to any route with a single decorator
- The CSS design system defined tokens (colors, spacing, transitions) that every component consumed consistently — changing `--clr-primary` once updated the entire UI
- Frontend animations (particles, scroll-reveal, 3D tilt) could be developed and tested independently of the backend

---

### If Given Another Month

If given an additional month, the following improvements would be prioritized:

1. **Real-time notifications** — WebSocket integration (via Flask-SocketIO) to push "Your Turn" alerts to the browser instantly without page reloads
2. **Image uploads** — Allow users to attach photos to listings using a cloud storage provider (Cloudinary / AWS S3)
3. **Offer history timeline** — A visual, chat-style thread showing the full negotiation history of each offer including timestamps and who made each move
4. **Watchlist / saved posts** — Let users bookmark listings they are interested in and receive notifications when they receive offers
5. **User profiles** — Public profile pages showing a user's reputation score, completed trades, and active listings
6. **Mobile-first PWA** — Convert to a Progressive Web App with offline capability and push notifications
7. **PostgreSQL migration** — Replace flat-file JSON with a proper relational database for production-grade concurrency and indexing

---

### Future Scope

TradePost has significant expansion potential beyond its current form:

**Platform Scale**
- Multi-category marketplace with structured item taxonomies (Electronics, Music, Books, etc.)
- Location-based filtering so users can find nearby trades and arrange in-person exchanges
- Multi-item bundle offers — propose trading a set of items rather than a single item

**Trust & Safety**
- User verification and reputation system with star ratings after each completed trade
- Flagging and moderation system for fraudulent or misleading listings
- Escrow-style "trade confirmation" — both parties confirm receipt before the offer is marked fully closed

**Monetisation (without breaking the barter model)**
- Premium listings with featured placement
- Optional escrow service for high-value trades
- TradePost API for third-party barter marketplace integrations

**AI Enhancements**
- Auto-suggestion of fair counter-offers based on comparable listings
- Item description generator from uploaded photos
- Smart matching — proactively notify users when a listing appears that matches their previously stated wants

In a world increasingly focused on sustainability and circular economies, TradePost is positioned to become a serious platform for reducing waste and democratising access to goods through the oldest form of trade: direct exchange.

---

*Built with Flask · PyJWT · Vanilla CSS · Vanilla JS · Canvas API*
