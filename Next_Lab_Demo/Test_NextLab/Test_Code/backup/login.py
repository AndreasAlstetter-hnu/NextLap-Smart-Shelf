import hashlib
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
from cryptography.fernet import Fernet
import requests

# Festes Masterpasswort im Code
MASTER_PASSWORD = "1234"

# Funktion zum Generieren eines Verschlüsselungsschlüssels und Speichern in einer Datei
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Funktion zum Laden des Verschlüsselungsschlüssels aus einer Datei
def load_key():
    return open("secret.key", "rb").read()

# Funktion zum Hashen des Passworts
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Funktion zum Verschlüsseln der Benutzerdatenbank
def encrypt_database(database, key):
    fernet = Fernet(key)
    json_data = json.dumps(database)
    encrypted_data = fernet.encrypt(json_data.encode())
    with open("user_database.enc", "wb") as file:
        file.write(encrypted_data)

# Funktion zum Entschlüsseln der Benutzerdatenbank
def decrypt_database(key):
    try:
        fernet = Fernet(key)
        with open("user_database.enc", "rb") as file:
            encrypted_data = file.read()
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return json.loads(decrypted_data)
    except FileNotFoundError:
        return {}  # Wenn die Datei nicht gefunden wird, geben wir eine leere Datenbank zurück

# Funktion zum Überprüfen der Anmeldedaten
def check_login(username, password):
    database = decrypt_database(key)
    if username in database:
        hashed_password = hash_password(password)
        if database[username] == hashed_password:
            return True
    return False

# Funktion zum Überprüfen des Masterpassworts
def check_master_password(password):
    return password == MASTER_PASSWORD

# Funktion zum Hinzufügen eines neuen Benutzers
def add_user(username, password):
    database = decrypt_database(key)
    if username in database:
        messagebox.showerror("Fehler", "Benutzername bereits vorhanden!")
    else:
        database[username] = hash_password(password)
        encrypt_database(database, key)
        messagebox.showinfo("Erfolg", "Neuer Benutzer hinzugefügt!")

# Funktion zum automatischen Schließen der Messagebox
def auto_close_messagebox(title, message, timeout):
    popup = tk.Toplevel()
    popup.title(title)
    label = tk.Label(popup, text=message)
    label.pack(pady=10, padx=10)
    popup.after(timeout, popup.destroy)
    popup.mainloop()

# Funktion zum Anzeigen des Willkommens-Popups
def show_welcome_popup(username):
    popup = tk.Toplevel()
    popup.title("Willkommen")

    label = tk.Label(popup, text=f"Willkommen, {username}!")
    label.pack(pady=20, padx=20)

    # Schließt das Popup nach 2 Sekunden und öffnet das Hauptfenster
    popup.after(2000, lambda: [popup.destroy(), login_window.destroy(), open_main_gui()])

# Haupt-GUI anzeigen
def open_main_gui():
    main_window = tk.Tk()
    main_window.title("Bedarfsmeldungen Supermarkt")
    main_window.geometry("500x400")
    # URLs for the server endpoints
    #delete_url = 'http://217.238.224.242:8310/Drohnen_GmbH'
    #get_url = 'http://217.238.224.242:8310/main.json'
    delete_url ='http://172.16.100.50:8310/Drohnen_GmbH'
    get_url = 'http://172.16.100.50:8310/main.json'
    # Function to send DELETE request with JSON data
    def send_delete_request(key, value):
        try:
            # Creating the JSON payload
            delete_data = {'key': key, 'value': value}

            # Sending the DELETE request with JSON data
            response = requests.delete(delete_url, json=delete_data)
            
            # Check if the request was successful
            if response.status_code == 200:
                print('Response from server:')
                print('Status code:', response.status_code)
                print('Response text:', response.text)
            else:
                print('Error deleting data:')
                print('Status code:', response.status_code)
                print('Response text:', response.text)
        except requests.exceptions.RequestException as e:
            print(f'Request error: {e}')

    # Function to send GET request to retrieve main.json
    def get_main_json():
        try:
            # Sending the GET request to retrieve main.json
            response = requests.get(get_url)
            
            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                print('Error retrieving main.json:')
                print('Status code:', response.status_code)
                print('Response text:', response.text)
                textbox.insert(tk.END,response.text)
        except requests.exceptions.RequestException as e:
            print(f'Request error: {e}')
        try:
            return response.text
        except:
            return "Server offline"

    def button_action_load():
        textbox.delete(1.0,tk.END)
        list_textbox=[]
        json_datei = get_main_json()
        if type(json_datei)== str:
            print(json_datei)
            textbox.insert(tk.END,json_datei+"\n")
        # JSON-Inhalt formatieren und in die Textbox einfügen
        formatted_json = json.dumps(json_datei, indent=4)
        formatted_json = formatted_json.split("\n")
        for i in range(0,len(formatted_json)):
            if ":" in formatted_json[i]:
                list_textbox.append(formatted_json[i])
        for i in range(0,len(list_textbox)):
            print(list_textbox[i])
            list_textbox[i]=list_textbox[i].replace(" ","")
            if "," in list_textbox[i]:
                list_textbox[i]=list_textbox[i].replace(",","")
            print(list_textbox[i])
        for i in range(0,len(list_textbox)):
            textbox.insert(tk.END, list_textbox[i]+"\n")


    def delete_auftrag():
        open_popup()
        textbox.insert(tk.END,"Buchungen abgeschlossen"+"\n")
        
    def close_popup():
        for i in range(0,len(list_pairs)):
            try:
                main_window.after(1000, send_delete_request(list_pairs[i][0],list_pairs[i][1]))
            except:
                textbox.insert(tk.END,f"key:{list_pairs[i][0]} und value {list_pairs[i][1]} konnten nicht entfernt werden"+"\n")
        popup_b.destroy()

    def open_popup():
        global list_pairs
        list_pairs=[]
        global popup_b
        popup_b = tk.Toplevel(main_window)
        popup_b.title("Buchungen")
        
        tk.Label(popup_b, text="Key:").grid(row=0, column=0, padx=10, pady=10)
        tk.Label(popup_b, text="Value:").grid(row=1, column=0, padx=10, pady=10)
        
        global key_entry
        key_entry = tk.Entry(popup_b)
        key_entry.grid(row=0, column=1, padx=10, pady=10)
        
        global value_entry
        value_entry = tk.Entry(popup_b)
        value_entry.grid(row=1, column=1, padx=10, pady=10)
        
        add_button = tk.Button(popup_b, text="Buchung hinzufügen", command=add_pair)
        add_button.grid(row=2, columnspan=2, pady=10)
        
        done_button = tk.Button(popup_b, text="Buchen", command=close_popup)
        done_button.grid(row=3, columnspan=2, pady=10)

    def add_pair():
        key = key_entry.get()
        value = value_entry.get()
        
        if key and value:
            list_pairs.append([key,value])
            print(list_pairs)
        else:
            messagebox.showwarning("Input Error", "Both fields must be filled out")  

    menubar = tk.Menu(main_window)
    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Datei", menu=filemenu)
    filemenu.add_command(label="Neuer Benutzer", command=create_user)
    main_window.config(menu=menubar)

    eingabe_frame = tk.Frame(main_window,height=100)
    textbox_frame = tk.Frame(main_window,height=400)
    eingabe_frame.pack(side="top")
    textbox_frame.pack(side="top")


    label = tk.Label(eingabe_frame, text="Willkommen!")
    label.pack(side="left",pady=20)

    button_load = tk.Button(eingabe_frame,text="Bedarf laden",command=button_action_load)
    button_load.pack(side="left",padx=50)
    button_delete =tk.Button(eingabe_frame,text="Buchung durchführen",command=delete_auftrag)
    button_delete.pack(side='left')
    # Rahmen für Textbox und Scrollbar
    frame = tk.Frame(textbox_frame)
    frame.pack(fill=tk.BOTH, expand=1)

    # Scrollbar erstellen
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Textbox erstellen
    textbox = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    textbox.pack(fill=tk.BOTH, expand=1)

    # Scrollbar mit Textbox verbinden
    scrollbar.config(command=textbox.yview)

    # JSON-Datei lesen
    with open("data.json", 'r') as file:
        data = json.load(file)

    

    main_window.mainloop()



# Login-Funktion
def login():
    username = entry_username.get()
    password = entry_password.get()

    if check_login(username, password):
        show_welcome_popup(username)
    elif check_master_password(password):
        show_welcome_popup(username)
    else:
        auto_close_messagebox("Login fehlgeschlagen", "Ungültiger Benutzername oder Passwort.", 2000)  # 2000 ms = 2 s

# Funktion zum Anzeigen des Popups für die Benutzererstellung
def create_user():
    master_password = simpledialog.askstring("Masterpasswort", "Bitte Masterpasswort eingeben:", show='*')
    if not master_password:
        return

    if check_master_password(master_password):
        username = simpledialog.askstring("Neuer Benutzer", "Benutzername eingeben:")
        if not username:
            return
        password = simpledialog.askstring("Neuer Benutzer", "Passwort eingeben:", show='*')
        if not password:
            return
        add_user(username, password)
    else:
        messagebox.showerror("Fehler", "Falsches Masterpasswort!")

# Überprüfen, ob der Schlüssel vorhanden ist, wenn nicht, einen neuen Schlüssel generieren
if not os.path.exists("secret.key"):
    generate_key()

# Schlüssel laden
key = load_key()

# Login-Fenster erstellen
login_window = tk.Tk()
login_window.title("Login-System")
login_window.geometry("300x200")

# Benutzername Label und Eingabefeld
label_username = tk.Label(login_window, text="Benutzername:")
label_username.pack(pady=5)
entry_username = tk.Entry(login_window)
entry_username.pack(pady=5)

# Passwort Label und Eingabefeld
label_password = tk.Label(login_window, text="Passwort:")
label_password.pack(pady=5)
entry_password = tk.Entry(login_window, show="*")
entry_password.pack(pady=5)

# Login Button
login_button = tk.Button(login_window, text="Login", command=login)
login_button.pack(pady=20)

# Tkinter Hauptschleife starten
login_window.mainloop()
