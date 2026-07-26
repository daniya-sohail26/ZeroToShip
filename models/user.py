import hashlib
import os
import json


class User:
    """
    Represents a registered user in the TradePost system.

    Passwords are never stored in plaintext — they are salted and hashed
    using SHA-256 before being persisted to the flat-file store.
    """

    def __init__(self, user_id: int, username: str, password_hash: str, salt: str):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.salt = salt

    # ------------------------------------------------------------------
    # Password utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Return the hex digest of SHA-256(salt + password)."""
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    @classmethod
    def create(cls, user_id: int, username: str, plain_password: str) -> "User":
        """
        Factory method that accepts a plaintext password, generates a random
        salt, hashes the password, and returns a fully initialised User object.
        """
        salt = os.urandom(16).hex()          # 32-char hex salt
        password_hash = cls._hash_password(plain_password, salt)
        return cls(user_id=user_id, username=username,
                   password_hash=password_hash, salt=salt)

    def verify_password(self, plain_password: str) -> bool:
        """Return True when *plain_password* matches the stored hash."""
        return self._hash_password(plain_password, self.salt) == self.password_hash

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the User into a JSON-safe dictionary."""
        return {
            "user_id":       self.user_id,
            "username":      self.username,
            "password_hash": self.password_hash,
            "salt":          self.salt,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Reconstruct a User from a stored dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password_hash=data["password_hash"],
            salt=data["salt"],
        )

    def public_dict(self) -> dict:
        """Return only safe fields — never expose password_hash or salt."""
        return {
            "user_id":  self.user_id,
            "username": self.username,
        }


# ------------------------------------------------------------------
# Flat-file user store
# ------------------------------------------------------------------

USER_DB_FILE = "users_db.json"


class UserStore:
    """
    Thin persistence layer for User objects, backed by a JSON flat-file.
    Mirrors the SerializationEngine pattern from Phase 1.
    """

    def __init__(self, filepath: str = USER_DB_FILE):
        self.filepath = filepath

    def _load_raw(self) -> list[dict]:
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save_raw(self, users: list[dict]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    def all(self) -> list[User]:
        """Return every persisted User."""
        return [User.from_dict(u) for u in self._load_raw()]

    def find_by_username(self, username: str) -> User | None:
        """Case-sensitive username lookup; returns None when not found."""
        for u in self.all():
            if u.username == username:
                return u
        return None

    def find_by_id(self, user_id: int) -> User | None:
        """User-ID lookup; returns None when not found."""
        for u in self.all():
            if u.user_id == user_id:
                return u
        return None

    def save(self, user: User) -> None:
        """Persist a new User (does not update existing records)."""
        raw = self._load_raw()
        raw.append(user.to_dict())
        self._save_raw(raw)

    def next_id(self) -> int:
        """Auto-increment: return max existing user_id + 1, or 1 if empty."""
        ids = [u["user_id"] for u in self._load_raw()]
        return max(ids) + 1 if ids else 1
