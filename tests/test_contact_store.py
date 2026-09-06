import json
import tempfile
import unittest
from pathlib import Path

from contact_store import Contact, ContactError, ContactStore


class ContactValidationTests(unittest.TestCase):
    def test_normalizes_contact_fields(self) -> None:
        contact = Contact.create("  Alice  ", "+91 98765 43210", " ALICE@EXAMPLE.COM ", " Home ")
        self.assertEqual(contact.name, "Alice")
        self.assertEqual(contact.email, "alice@example.com")

    def test_rejects_invalid_phone_and_email(self) -> None:
        with self.assertRaises(ContactError):
            Contact.create("Alice", "12")
        with self.assertRaises(ContactError):
            Contact.create("Alice", "9876543210", "invalid-email")


class ContactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "contacts.json"
        self.store = ContactStore(self.path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_add_load_search_update_and_delete(self) -> None:
        self.store.add(Contact.create("Alice", "9876543210", "alice@example.com"))
        self.store.add(Contact.create("Bob", "+91 99887 76655"))

        loaded = ContactStore(self.path)
        self.assertIsNone(loaded.load())
        self.assertEqual([contact.name for contact in loaded.search("9876")], ["Alice"])

        loaded.update("Alice", Contact.create("Alice Roy", "9876543210"))
        self.assertEqual([contact.name for contact in loaded.all()], ["Alice Roy", "Bob"])

        loaded.delete("Bob")
        self.assertEqual([contact.name for contact in loaded.all()], ["Alice Roy"])

    def test_duplicate_name_is_case_insensitive(self) -> None:
        self.store.add(Contact.create("Alice", "9876543210"))
        with self.assertRaises(ContactError):
            self.store.add(Contact.create("ALICE", "9988776655"))

    def test_invalid_json_is_backed_up(self) -> None:
        self.path.write_text("not json", encoding="utf-8")
        notice = self.store.load()
        self.assertIn("Invalid contact data", notice or "")
        self.assertFalse(self.path.exists())
        self.assertEqual(len(list(self.path.parent.glob("contacts.corrupt-*.json"))), 1)

    def test_saved_json_contains_expected_fields(self) -> None:
        self.store.add(Contact.create("Alice", "9876543210"))
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload[0]["name"], "Alice")
        self.assertEqual(payload[0]["email"], "")


if __name__ == "__main__":
    unittest.main()
