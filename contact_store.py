"""Validation and local JSON persistence for the contact-book application."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 ()-]{5,19}$")


class ContactError(ValueError):
    """Raised when contact input or stored data is invalid."""


@dataclass(frozen=True, slots=True)
class Contact:
    name: str
    phone: str
    email: str = ""
    address: str = ""

    @classmethod
    def create(cls, name: str, phone: str, email: str = "", address: str = "") -> "Contact":
        name = name.strip()
        phone = phone.strip()
        email = email.strip().lower()
        address = address.strip()

        if not name:
            raise ContactError("Name is required.")
        if len(name) > 80:
            raise ContactError("Name must contain 80 characters or fewer.")
        if not PHONE_PATTERN.fullmatch(phone):
            raise ContactError("Enter a valid phone number using 6 to 20 characters.")
        if email and not EMAIL_PATTERN.fullmatch(email):
            raise ContactError("Enter a valid email address or leave it blank.")
        if len(address) > 300:
            raise ContactError("Address must contain 300 characters or fewer.")

        return cls(name=name, phone=phone, email=email, address=address)


class ContactStore:
    """Store contacts in a JSON file with validation and atomic writes."""

    def __init__(self, path: str | Path = "contacts.json") -> None:
        self.path = Path(path)
        self._contacts: dict[str, Contact] = {}

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().casefold()

    def load(self) -> str | None:
        """Load contacts and return a recovery notice when corrupt data is backed up."""
        if not self.path.exists():
            self._contacts = {}
            return None

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ContactError("The contact file must contain a list.")

            loaded: dict[str, Contact] = {}
            for item in raw:
                if not isinstance(item, dict):
                    raise ContactError("Every saved contact must be an object.")
                contact = Contact.create(
                    str(item.get("name", "")),
                    str(item.get("phone", "")),
                    str(item.get("email", "")),
                    str(item.get("address", "")),
                )
                key = self._key(contact.name)
                if key in loaded:
                    raise ContactError(f"Duplicate saved contact: {contact.name}")
                loaded[key] = contact
        except (OSError, UnicodeError, json.JSONDecodeError, ContactError, TypeError) as error:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = self.path.with_name(f"contacts.corrupt-{timestamp}.json")
            try:
                self.path.replace(backup)
            except OSError as backup_error:
                raise ContactError(f"Could not read or back up the contact file: {backup_error}") from error
            self._contacts = {}
            return f"Invalid contact data was moved to {backup.name}."

        self._contacts = loaded
        return None

    def all(self) -> list[Contact]:
        return sorted(self._contacts.values(), key=lambda contact: contact.name.casefold())

    def add(self, contact: Contact) -> None:
        key = self._key(contact.name)
        if key in self._contacts:
            raise ContactError(f"A contact named {contact.name} already exists.")
        self._contacts[key] = contact
        self.save()

    def update(self, original_name: str, contact: Contact) -> None:
        original_key = self._key(original_name)
        if original_key not in self._contacts:
            raise ContactError("The selected contact no longer exists.")

        new_key = self._key(contact.name)
        if new_key != original_key and new_key in self._contacts:
            raise ContactError(f"A contact named {contact.name} already exists.")

        del self._contacts[original_key]
        self._contacts[new_key] = contact
        self.save()

    def delete(self, name: str) -> None:
        key = self._key(name)
        if key not in self._contacts:
            raise ContactError("The selected contact no longer exists.")
        del self._contacts[key]
        self.save()

    def search(self, query: str) -> list[Contact]:
        normalized = query.strip().casefold()
        if not normalized:
            return []
        return [
            contact
            for contact in self.all()
            if normalized in contact.name.casefold() or normalized in contact.phone.casefold()
        ]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        payload: Iterable[dict[str, str]] = (asdict(contact) for contact in self.all())
        try:
            temporary_path.write_text(
                json.dumps(list(payload), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError as error:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise ContactError(f"Could not save contacts: {error}") from error
