import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import json

API_URL = "http://localhost:8310/Drohnen_GmbH"  # Lokaler Server
HEADERS = {"Content-Type": "application/json"}

def get_orders():
    try:
        r = requests.get(API_URL)
        r.raise_for_status()
        data = r.json()
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, json.dumps(data, indent=4))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def post_order():
    try:
        order_data = json.loads(post_entry.get("1.0", tk.END))
        r = requests.post(API_URL, headers=HEADERS, json=order_data)
        r.raise_for_status()
        response = r.json()
        messagebox.showinfo("Success", f"Order gesendet!\n{response}")
        post_entry.delete("1.0", tk.END)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_order():
    try:
        order_data = json.loads(delete_entry.get("1.0", tk.END))
        r = requests.delete(API_URL, headers=HEADERS, json=order_data)
        r.raise_for_status()
        response = r.json()
        messagebox.showinfo("Success", f"Order gelöscht!\n{response}")
        delete_entry.delete("1.0", tk.END)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --- GUI ---
root = tk.Tk()
root.title("Drohnen GmbH API GUI")
root.geometry("700x600")

# GET
tk.Label(root, text="Alle Orders abrufen (GET)").pack()
tk.Button(root, text="Abrufen", command=get_orders).pack()
output_text = scrolledtext.ScrolledText(root, height=15)
output_text.pack(fill=tk.BOTH, expand=True)

# POST
tk.Label(root, text="Neue Order erstellen (POST) - JSON eingeben:").pack()
post_entry = scrolledtext.ScrolledText(root, height=5)
post_entry.pack(fill=tk.BOTH, expand=True)
tk.Button(root, text="Senden", command=post_order).pack()

# DELETE
tk.Label(root, text="Order löschen (DELETE) - JSON mit 'order_id' oder 'number':").pack()
delete_entry = scrolledtext.ScrolledText(root, height=5)
delete_entry.pack(fill=tk.BOTH, expand=True)
tk.Button(root, text="Löschen", command=delete_order).pack()

root.mainloop()
