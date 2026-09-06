"""Tkinter desktop interface for the Contact Book project."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from contact_store import Contact, ContactError, ContactStore


class ContactBookApp(tk.Tk):
    def __init__(self, store: ContactStore) -> None:
        super().__init__()
        self.store = store
        self.visible_contacts: list[Contact] = []

        self.title("Contact Book")
        self.geometry("720x560")
        self.minsize(620, 500)
        self.configure(padx=20, pady=20)

        self.name = tk.StringVar()
        self.phone = tk.StringVar()
        self.email = tk.StringVar()
        self.address = tk.StringVar()
        self.search_text = tk.StringVar()

        self._build_ui()
        recovery_notice = self.store.load()
        self.refresh_list()
        if recovery_notice:
            messagebox.showwarning("Contact data recovered", recovery_notice, parent=self)

    def _build_ui(self) -> None:
        title = ttk.Label(self, text="Contact Book", font=("Arial", 22, "bold"))
        title.pack(anchor="w", pady=(0, 14))

        form = ttk.LabelFrame(self, text="Contact details", padding=12)
        form.pack(fill="x")

        fields = (
            ("Name *", self.name),
            ("Phone *", self.phone),
            ("Email", self.email),
            ("Address", self.address),
        )
        for row, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Entry(form, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
        form.columnconfigure(1, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Add", command=self.add_contact).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Update selected", command=self.update_contact).pack(side="left", padx=8)
        ttk.Button(actions, text="Delete selected", command=self.delete_contact).pack(side="left", padx=8)
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left", padx=8)

        search = ttk.Frame(self)
        search.pack(fill="x", pady=(2, 8))
        ttk.Label(search, text="Search").pack(side="left", padx=(0, 8))
        search_entry = ttk.Entry(search, textvariable=self.search_text)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_list())

        self.listbox = tk.Listbox(self, height=12, activestyle="dotbox")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.populate_selected)

        self.status = ttk.Label(self, text="0 contacts")
        self.status.pack(anchor="w", pady=(8, 0))

    def _contact_from_form(self) -> Contact | None:
        try:
            return Contact.create(
                self.name.get(), self.phone.get(), self.email.get(), self.address.get()
            )
        except ContactError as error:
            messagebox.showwarning("Check contact details", str(error), parent=self)
            return None

    def _selected_contact(self) -> Contact | None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Select a contact", "Choose a contact from the list first.", parent=self)
            return None
        return self.visible_contacts[selection[0]]

    def add_contact(self) -> None:
        contact = self._contact_from_form()
        if not contact:
            return
        try:
            self.store.add(contact)
        except ContactError as error:
            messagebox.showerror("Could not add contact", str(error), parent=self)
            return
        self.clear_form()
        self.refresh_list()

    def update_contact(self) -> None:
        selected = self._selected_contact()
        if not selected:
            return
        updated = self._contact_from_form()
        if not updated:
            return
        try:
            self.store.update(selected.name, updated)
        except ContactError as error:
            messagebox.showerror("Could not update contact", str(error), parent=self)
            return
        self.clear_form()
        self.refresh_list()

    def delete_contact(self) -> None:
        selected = self._selected_contact()
        if not selected:
            return
        confirmed = messagebox.askyesno(
            "Delete contact", f"Delete {selected.name}?", parent=self
        )
        if not confirmed:
            return
        try:
            self.store.delete(selected.name)
        except ContactError as error:
            messagebox.showerror("Could not delete contact", str(error), parent=self)
            return
        self.clear_form()
        self.refresh_list()

    def populate_selected(self, _event: tk.Event[tk.Misc]) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        contact = self.visible_contacts[selection[0]]
        self.name.set(contact.name)
        self.phone.set(contact.phone)
        self.email.set(contact.email)
        self.address.set(contact.address)

    def clear_form(self) -> None:
        for variable in (self.name, self.phone, self.email, self.address):
            variable.set("")
        self.listbox.selection_clear(0, tk.END)

    def refresh_list(self) -> None:
        query = self.search_text.get()
        self.visible_contacts = self.store.search(query) if query.strip() else self.store.all()
        self.listbox.delete(0, tk.END)
        for contact in self.visible_contacts:
            details = f"{contact.name} — {contact.phone}"
            if contact.email:
                details += f" — {contact.email}"
            self.listbox.insert(tk.END, details)
        self.status.configure(text=f"{len(self.visible_contacts)} contact(s) shown")


def main() -> None:
    data_path = Path(__file__).with_name("contacts.json")
    app = ContactBookApp(ContactStore(data_path))
    app.mainloop()


if __name__ == "__main__":
    main()
