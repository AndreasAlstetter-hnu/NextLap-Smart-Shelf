import json
import logging
import random
import requests
import os, sys


from http.server import BaseHTTPRequestHandler, HTTPServer


PORT = int(os.environ.get("NEXTLAB_PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8310))
# ... starte deinen Server auf PORT ...


# ------------------ Konfiguration ------------------
API_BASE = "https://hnu.nextlap.io"
TIMEOUT = 10 # Sekunden für HTTP-Requests
VERIFY_TLS = True # Bei Bedarf auf Zertifikatsprobleme mit False testen (nicht empfohlen)
#HEADERS = {"Authorization": "Bearer <TOKEN>"}  # Falls Auth nötig: einkommentieren
HEADERS = {}


BEDARF_FILE = "data.json" # lokale Datei im von dir gezeigten Format
# PORT = 8310                   # lokaler Adapter-Port für deine GUI
# ---------------------------------------------------

LAST_ORDER = {"id": None, "number": None}

logging.basicConfig(filename='server.log', level=logging.INFO,
format='%(asctime)s - %(levelname)s - %(message)s')



def load_bedarf_from_file(path=BEDARF_FILE):

    """
    Lädt eine lokale Datei im von dir gezeigten Format.
    :param path: Der Pfad zur Datei (standardmäßig "data.json")
    :type path: str
    :return: Die geladene Datei im JSON-Format
    :rtype: dict
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def build_order_payload_from_bedarf(bedarf: dict) -> dict:

    """
    Builds a payload for an order from a bedarf (JSON-Format).
    
    The payload will contain the order number and a list of items.
    
    The order number will be a random 6-digit number if no number is given in the bedarf.
    
    The items will be filtered according to the following rules:
    
        - If the item number is empty, it will be skipped.
        - If the item number contains any characters other than letters, numbers and underscores, it will be skipped.
    
    If no items remain after filtering, a ValueError will be raised.
    
    If any invalid items were skipped, a warning will be printed to the console.
    
    :param bedarf: The bedarf (JSON-Format) to build the payload from.
    :type bedarf: dict
    :return: The built payload.
    :rtype: dict
    :raises ValueError: If no items remain after filtering.
    """
    import re
    order_number = str(bedarf.get("number") or ''.join(random.choices('0123456789', k=6)))
    raw_items = bedarf.get("items", [])


    items = []
    invalid_items = []


    for it in raw_items:
        num = str(it.get("number") or "").strip()
        if not num:
            continue
        if not re.match(r'^[A-Za-z0-9_]+$', num):
            invalid_items.append(num)
            continue
        items.append({"number": num})


    if not items:
        raise ValueError(f"Keine gültigen Items im Bedarf! Ungültige Artikelnummern: {invalid_items}")


    if invalid_items:
        print(f"Warnung: Ungültige Artikelnummern wurden ignoriert: {invalid_items}")


    return {"number": order_number, "items": items}




def api_get_orders():
    """
    Liefert eine Liste aller Aufträge des Ziel-API
    https://hnu.nextlab.io
    :return: Liste der Aufträge im JSON-Format
    :rtype: dict
    """
    url = f"{API_BASE}/v1/orders/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    return r.json()



def api_retrieve_order_by_number_or_id(order_identifier: str):

    """
    Liefert einen Auftrag anhand seiner ID oder Nummer vom Ziel-API.
    :param order_identifier: Die ID oder die Nummer des Auftrags
    :type order_identifier: str
    :return: Der Auftrag im JSON-Format
    :rtype: dict
    """

    url = f"{API_BASE}/v1/orders/{order_identifier}/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    if r.status_code == 200:
        return r.json()
    r.raise_for_status()
    return r.json()



def api_delete_order_by_id(order_id: int):
    """
    Löscht den Auftrag mit der angegebenen ID.
    :param order_id: Die ID des Auftrags
    :type order_id: int
    :return: True, wenn der Auftrag erfolgreich gelöscht wurde, sonst False
    :rtype: bool
    """
    url = f"{API_BASE}/v1/orders/{order_id}/"
    r = requests.delete(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    # API antwortet bei Erfolg leer; 204/200 sind ok
    if r.status_code in (200, 204):
        return True
    r.raise_for_status()
    return False

def api_get_order_status(order_identifier: str):

    """
    Gibt den Status eines Auftrags zurück.
    :param order_identifier: Die ID oder die Nummer des Auftrags
    :type order_identifier: str
    :return: Ein Dictionary mit den Keys "id", "number" und "status"
    :rtype: dict
    """
    url = f"{API_BASE}/v1/orders/{order_identifier}/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    data = r.json()
    print(data)
    return {
        "id": data.get("id"),
        "number": data.get("number"),
        "status": data.get("status")
    }

def api_create_order(payload: dict):
    """
    Erstellt einen neuen Auftrag auf dem Ziel-API.
    :param payload: Die Payload im JSON-Format
    :type payload: dict
    :return: Der erstellte Auftrag im JSON-Format
    :rtype: dict
    """
    global LAST_ORDER
    url = f"{API_BASE}/v1/orders/"
    r = requests.post(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=TIMEOUT,
        verify=VERIFY_TLS
    )
    r.raise_for_status()
    created = r.json()  # {"id": int}
    LAST_ORDER["id"] = created.get("id")
    LAST_ORDER["number"] = payload.get("number")
    return created



class PickingAdapterHandler(BaseHTTPRequestHandler):


    def _send_json(self, status, obj):
        """
        Sends a JSON response with the given status and object.

        :param status: The HTTP status code to send
        :param obj: The object to serialize into JSON
        :type status: int
        :type obj: dict
        :return: None
        :rtype: None
        """
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))


    def do_GET(self):

        """
        Handles a GET request to /Drohnen_GmbH.

        If there is no current order, returns a 404 error with a JSON body containing the error "Kein aktueller Auftrag bekannt".

        Otherwise, retrieves the status of the current order using the API and sends it back as a JSON response.

        If there is an error during the API call, sends back the error as a JSON response with the same status code as the error.

        If there is any other exception, sends back a 500 error with a JSON body containing the error message.

        :return: None
        :rtype: None
        """
        if self.path == "/Drohnen_GmbH":
            try:
                if not LAST_ORDER["id"] and not LAST_ORDER["number"]:
                    return self._send_json(404, {"error": "Kein aktueller Auftrag bekannt"})

                identifier = str(LAST_ORDER["id"] or LAST_ORDER["number"])
                status_info = api_get_order_status(identifier)
                self._send_json(200, status_info)
            except requests.HTTPError as e:
                self._send_json(e.response.status_code, {"error": str(e), "body": e.response.text})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


    def do_POST(self):
        """
        Handles a POST request to /Drohnen_GmbH.

        If there is a JSON body, it is expected to contain the order data in the format returned by load_bedarf_from_file().
        If the body is empty, the function will attempt to load the order data from the file specified in BEDARF_FILE.

        If the file is not found, the function will return a 400 error with a JSON body containing the error message.

        If there is an error during the API call, the function will return the error as a JSON response with the same status code as the error.

        If there is any other exception, the function will return a 500 error with a JSON body containing the error message.

        :return: None
        :rtype: None
        """
        if self.path == "/Drohnen_GmbH":
            try:
                bedarf = load_bedarf_from_file()
                payload = build_order_payload_from_bedarf(bedarf)
                created = api_create_order(payload)
                self._send_json(200, {"created_order": created, "payload": payload})
            except requests.HTTPError as e:
                self._send_json(e.response.status_code, {"error": str(e), "body": e.response.text})
            except FileNotFoundError:
                self._send_json(400, {"error": f"{BEDARF_FILE} nicht gefunden"})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


    def do_DELETE(self):
        """
        Handles a DELETE request to /Drohnen_GmbH.

        If there is a JSON body, it is expected to contain the order data in the format returned by load_bedarf_from_file().
        If the body is empty, the function will attempt to load the order data from the file specified in BEDARF_FILE.

        If the file is not found, the function will return a 400 error with a JSON body containing the error message.

        If there is an error during the API call, the function will return the error as a JSON response with the same status code as the error.

        If there is any other exception, the function will return a 500 error with a JSON body containing the error message.

        :return: None
        :rtype: None
        """
        if self.path == "/Drohnen_GmbH":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                req = json.loads(body or "{}")


                order_id = req.get("order_id")
                order_number = req.get("order_number")


                if not order_id and not order_number:
                    return self._send_json(400, {"error": "order_id oder order_number erforderlich"})


                if not order_id and order_number:
                    order = api_retrieve_order_by_number_or_id(str(order_number))
                    order_id = order.get("id")
                    if not order_id:
                        return self._send_json(404, {"error": f"Order {order_number} nicht gefunden"})


                ok = api_delete_order_by_id(int(order_id))
                if not ok:
                    return self._send_json(500, {"error": f"Löschen von Order {order_id} fehlgeschlagen"})


                # Neuen Auftrag erstellen
                bedarf = load_bedarf_from_file()
                payload = build_order_payload_from_bedarf(bedarf)
                created = api_create_order(payload)


                return self._send_json(200, {
                    "deleted_order_id": order_id,
                    "new_order": created,
                    "new_order_payload": payload
                 })


            except requests.HTTPError as e:
                self._send_json(e.response.status_code, {"error": str(e), "body": e.response.text})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()



if __name__ == "__main__":


    with HTTPServer(("0.0.0.0", PORT), PickingAdapterHandler) as httpd:
        logging.info(f"Adapter-Server gestartet auf Port {PORT}, Ziel: {API_BASE}")
        print(f"Adapter-Server läuft auf Port {PORT} → Ziel-API: {API_BASE}")
        httpd.serve_forever()
        

