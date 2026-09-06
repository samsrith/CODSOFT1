# Contact Book

A small desktop contact manager built with Python and Tkinter. It supports adding,
editing, deleting, listing, and searching contacts while storing data locally in
JSON format.

This project was created as a CodSoft Python programming task and later refined
to demonstrate validation, safe file handling, separation of concerns, and
automated tests.

## Features

- Add contacts with a name, phone number, email address, and postal address
- Search by name or phone number
- Update and delete selected contacts
- Prevent accidental replacement of an existing contact
- Validate names, phone numbers, and email addresses
- Recover gracefully when the local data file is empty or invalid
- Save changes atomically to reduce the risk of file corruption
- Keep personal contact data outside Git version control

## Project structure

| Path | Purpose |
|---|---|
| `contact_book.py` | Tkinter user interface and application entry point |
| `contact_store.py` | Validation and JSON persistence logic |
| `tests/test_contact_store.py` | Unit tests for the storage layer |

## Requirements

- Python 3.10 or newer
- Tkinter, normally included with standard Python desktop installations

No third-party Python packages are required.

## Run the application

```bash
python contact_book.py
```

Contacts are stored locally in `contacts.json` beside the program. That file is
ignored by Git because it may contain personal information.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

You can also check both Python files without launching the graphical interface:

```bash
python -m py_compile contact_book.py contact_store.py
```

## Security and privacy

This is a local learning project, not a production address-book service. The
JSON file is not encrypted, so do not use the application for highly sensitive
information or sync `contacts.json` to a public location. A production version
would use encrypted storage, authentication, backups, and a clear privacy model.

## Possible next improvements

1. Export and import contacts as CSV.
2. Add encrypted local storage.
3. Add keyboard shortcuts and improved accessibility.
4. Package the application as a desktop executable.
