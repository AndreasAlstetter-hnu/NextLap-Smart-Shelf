import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json

import os
PORT = int(os.environ.get("NEXTLAB_PORT", "8310"))
BASE_URL = f"http://127.0.0.1:{PORT}"
# ... überall BASE_URL verwenden ...

SERVER_URL = "http://localhost:8310/Drohnen_GmbH"  # Lokaler Adapter

class PickingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Picking-System GUI")
        self.geometry("800x500")

        # Buttons
        frm_buttons = tk.Frame(self)
        frm_buttons.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(frm_buttons, text="Aufträge laden", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        tk.Button(frm_buttons, text="Neuen Auftrag erstellen", command=self.create_order).pack(side=tk.LEFT, padx=5)
        tk.Button(frm_buttons, text="Auftrag löschen", command=self.delete_order).pack(side=tk.LEFT, padx=5)

        # Treeview für Aufträge
        self.tree = ttk.Treeview(self, columns=("id", "number", "status"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("number", text="Nummer")
        self.tree.heading("status", text="Status")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def load_orders(self):
        try:
            resp = requests.get(SERVER_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # Tree leeren
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Ergebnisse einfügen
            for order in data.get("results", []):
                self.tree.insert("", tk.END, values=(
                    order.get("id"),
                    order.get("number"),
                    order.get("status", "-")
                ))
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def create_order(self):
        try:
            resp = requests.post(SERVER_URL, timeout=5)  # kein "data.json" nötig
            resp.raise_for_status()
            data = resp.json()
            messagebox.showinfo(
                "Erfolg",
                f"Neuer Auftrag erstellt:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
            )
            self.load_orders()
        except requests.HTTPError as http_err:
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text
            messagebox.showerror(
                "HTTP-Fehler",
                f"Status: {resp.status_code}\nFehler: {http_err}\nBody: {err_body}"
            )
            print(http_err)
            print(err_body)
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen: {e}")



    def delete_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Hinweis", "Bitte zuerst einen Auftrag auswählen.")
            return

        order_values = self.tree.item(selected[0], "values")
        order_id = order_values[0]
        order_number = order_values[1]

        if not messagebox.askyesno("Bestätigung", f"Auftrag {order_number} löschen und neuen erstellen?"):
            return

        try:
            # Prüfen, ob ID wirklich eine Zahl ist
            try:
                payload = {"order_id": int(order_id)}
            except (ValueError, TypeError):
                # Falls nicht, ID weglassen und Nummer senden
                payload = {"order_number": str(order_number)}

            resp = requests.delete(SERVER_URL, json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            messagebox.showinfo(
                "Erfolg",
                f"Auftrag gelöscht und neuer erstellt:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
            )
            self.load_orders()

        except requests.HTTPError as http_err:
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text
            messagebox.showerror(
                "HTTP-Fehler",
                f"Status: {resp.status_code}\nFehler: {http_err}\nBody: {err_body}"
            )
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}")


if __name__ == "__main__":
    app = PickingGUI()
    app.mainloop()
