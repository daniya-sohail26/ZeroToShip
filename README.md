# TradePost — Peer-to-Peer Barter Exchange

A full-stack barter exchange platform where users post items, negotiate trades
through a turn-based counter-offer system, and close deals — no money involved.
Built across five phases from data models to a fully integrated web application.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.1 |
| Auth | PyJWT 2.10 (HS256, 24-hour tokens) |
| Persistence | Flat-file JSON (`tradepost_db.json`, `users_db.json`) |
| Frontend | Jinja2 templates, vanilla CSS (glassmorphism, CSS Grid), vanilla JS (fetch API) |
| Session | JWT stored in `localStorage` + `tp_token` cookie (read by Flask page routes) |

---

## Project Structure

```
Phase 2/
├── app.py                      # Application factory — entry point
├── requirements.txt
├── .gitignore
│
├── models/
│   ├── user.py                 # User model + salted SHA-256 password hashing
│   └── logic.py                # TradePost & NegotiationOffer models + TradeStore engine
│
├── views/
│   ├── auth.py                 # POST /auth/register  POST /auth/login
│   ├── routes.py               # REST API  /api/posts  /api/offers  …
│   └── pages.py                # HTML page routes  /  /dashboard  /login  /register
│
├── middleware/
│   └── auth_guard.py           # @token_required  @owner_required decorators
│
├── templates/
│   ├── base.html               # Shared layout (navbar, modals, footer)
│   ├── index.html              # Marketplace — live post grid
│   ├── dashboard.html          # Negotiation dashboard — live offer cards
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   └── 404.html                # Error page
│
└── static/
    ├── css/style.css           # Full design system (dark theme, glassmorphism)
    └── js/app.js               # Modals, toasts, filter/sort, live fetch() calls
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/daniya-sohail26/ZeroToShip.git
cd ZeroToShip
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `flask==3.1.1`, `PyJWT==2.10.1`

### 3. (Optional) Set environment variables

```bash
# Windows PowerShell
$env:JWT_SECRET = "your-long-random-secret-here"
$env:FLASK_DEBUG = "1"     # enables hot-reload
$env:PORT = "5000"         # default port
```

> The app runs without these set — it uses safe development defaults.

---

## Running the Application

```bash
python app.py
```

Then open your browser at:

```
http://127.0.0.1:5000
```

---

## Testing the Full Feature Set

### Step 1 — Register two accounts

Open two browser tabs (or use Postman alongside the browser).

**Tab 1 — Register Alice (post owner)**
- Go to `http://127.0.0.1:5000/register`
- Username: `alice`, Password: `secret123`
- You are redirected to the Marketplace.

**Tab 2 — Register Bob (bidder)**
- Open a private/incognito window → `http://127.0.0.1:5000/register`
- Username: `bob`, Password: `secret123`

---

### Step 2 — Create a listing (as Alice)

- Click **+ New Listing** in the navbar.
- Title: `Vintage Korg MS-20 Synthesizer`
- Description: `Semi-modular analog synth, excellent condition.`
- Click **Post Listing** — the card appears live in the grid.

---

### Step 3 — Submit an offer (as Bob)

- In Bob's window, go to `http://127.0.0.1:5000`
- Find Alice's listing and click **Make Offer**.
- Enter: `Roland TR-808 drum machine, mint condition.`
- Click **Submit Offer**.

---

### Step 4 — Respond as Alice (Your Turn)

- In Alice's window, go to `http://127.0.0.1:5000/dashboard`
- Alice's card shows a glowing **Your Turn** badge.
- Click **Counter** → enter: `Add the original power supply and we have a deal.`
- Click **Send Counter** — turn flips to Bob.

---

### Step 5 — Bob counters back

- In Bob's dashboard the card now shows **Your Turn**.
- Click **Counter** → enter: `Done — PSU included. Final offer.`
- Turn flips back to Alice.

---

### Step 6 — Accept + Auto-Decline

- Alice sees **Your Turn** again.
- Click **Accept** → confirm the dialog.
- The offer is accepted, the post closes, and any other pending offers on
  the same post are **auto-declined** in a single server-side pass.
- The response shows how many rival offers were declined (`auto_declined: N`).

---

### REST API (Postman)

All API endpoints return JSON and accept `Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | Liveness check |
| `POST` | `/auth/register` | — | Create account → JWT |
| `POST` | `/auth/login` | — | Login → JWT |
| `GET` | `/api/posts` | — | All listings (optional `?status=Open`) |
| `POST` | `/api/posts` | ✓ | Create listing |
| `GET` | `/api/posts/<id>` | ✓ | Single post |
| `GET` | `/api/posts/<id>/offers` | ✓ | All offers on a post |
| `POST` | `/api/offers` | ✓ | Submit offer |
| `PUT` | `/api/offers/<id>/counter` | ✓ | Counter (flips turn) |
| `PUT` | `/api/offers/<id>/accept` | ✓ | Accept + auto-decline rivals |
| `PUT` | `/api/offers/<id>/decline` | ✓ | Decline offer |

---

## Business Rules

- A user **cannot bid on their own post**.
- A user can only have **one active offer per post**.
- Only the **current `turn_holder`** can counter, accept, or decline.
- Accepting a trade **instantly closes the post** and **auto-declines all
  other Pending/Countered offers** on that post in one atomic write.

---

## Phase Summary

| Phase | Deliverable |
|---|---|
| 1 | `TradePost` and `NegotiationOffer` data models + flat-file serialisation engine |
| 2 | Flask server bootstrap, JWT auth (`/register`, `/login`), profile gatekeeper middleware |
| 3 | RESTful trading endpoints, turn-taking validator, auto-decline cascade |
| 4 | Static HTML/CSS UI — marketplace grid and negotiation dashboard with glow badges |
| 5 | Full integration — live Jinja2 templates, fetch() API wiring, premium UI overhaul |
