import json
import logging
import random
import requests
import threading


from http.server import BaseHTTPRequestHandler, HTTPServer
from mqtt_connection import MqttOrderClient


import os, sys
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


logging.basicConfig(filename='server.log', level=logging.INFO,
format='%(asctime)s - %(levelname)s - %(message)s')



def load_bedarf_from_file(path=BEDARF_FILE):
    """Lädt deinen Bedarf (dein JSON-Format) von der lokalen Datei."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def build_order_payload_from_bedarf(bedarf: dict) -> dict:
    """
    Baut die Payload exakt so, wie von dir gewünscht:
   {
    "number": "123456",
    "items": [{"number": "25"}, ...] } """
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
    url = f"{API_BASE}/v1/orders/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    return r.json()



def api_retrieve_order_by_number_or_id(order_identifier: str):
    """
    Versucht zuerst ID (Ganzzahl), sonst Nummer.
    API sagt: GET /v1/orders/{orderId or orderNumber}/
    """
    url = f"{API_BASE}/v1/orders/{order_identifier}/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    if r.status_code == 200:
        return r.json()
    r.raise_for_status()
    return r.json()



def api_delete_order_by_id(order_id: int):
    url = f"{API_BASE}/v1/orders/{order_id}/"
    r = requests.delete(url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_TLS)
    # API antwortet bei Erfolg leer; 204/200 sind ok
    if r.status_code in (200, 204):
        return True
    r.raise_for_status()
    return False



def api_create_order(payload: dict):
    url = f"{API_BASE}/v1/orders/"
    r = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"},
    data=json.dumps(payload), timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    return r.json() # {"id": int}



class PickingAdapterHandler(BaseHTTPRequestHandler):


    def _send_json(self, status, obj):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))


    def do_GET(self):
        if self.path == "/Drohnen_GmbH":
            try:
                data = api_get_orders()
                self._send_json(200, data)
            except requests.HTTPError as e:
                self._send_json(e.response.status_code, {"error": str(e), "body": e.response.text})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


    def do_POST(self):
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
        PickingAdapterHandler.do_POST(self)
        httpd.serve_forever()
        