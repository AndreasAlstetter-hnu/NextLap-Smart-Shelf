import os
import sys
import signal
import time
import logging
import threading
from http.server import HTTPServer
from server_API import PickingAdapterHandler
from mqtt_connection import MqttOrderClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_port(default=8310):
    # Port via Umgebungsvariable (NEXTLAB_PORT) > CLI-Arg > Default
    if "NEXTLAB_PORT" in os.environ:
        return int(os.environ["NEXTLAB_PORT"])
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    return default

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True  # schnelleres Rebind bei Neustarts

def start_http_server(port: int):
    httpd = ReusableHTTPServer(("0.0.0.0", port), PickingAdapterHandler)
    t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.5}, name="http-server", daemon=False)
    t.start()
    logging.info(f"HTTP-Server gestartet auf Port {port} (Thread {t.name})")
    return httpd, t

def start_mqtt_client():
    client = MqttOrderClient()
    t = threading.Thread(target=client.start, name="mqtt-client", daemon=False)  # client.start() blockiert, bis stop()
    t.start()
    logging.info(f"MQTT-Client gestartet (Thread {t.name})")
    return client, t

def main():
    port = get_port()
    stop_evt = threading.Event()

    def on_signal(sig, frame):
        logging.info(f"Signal {sig} empfangen – fahre Dienste sauber herunter …")
        stop_evt.set()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, on_signal)
        except Exception:
            pass  # z. B. eingeschränkt unter Windows

    httpd = None
    http_thread = None
    mqtt = None
    mqtt_thread = None

    try:
        # HTTP zuerst (wenn Port belegt -> Exception, wird geloggt und wir fahren trotzdem MQTT hoch)
        try:
            httpd, http_thread = start_http_server(port)
        except OSError as e:
            logging.error(f"HTTP-Server konnte Port {port} nicht binden: {e}. HTTP wird übersprungen.")

        # Dann MQTT
        try:
            mqtt, mqtt_thread = start_mqtt_client()
        except Exception as e:
            logging.exception(f"MQTT-Client Startfehler: {e}")

        # Hauptloop bis STRG+C / Stop-BAT
        while not stop_evt.is_set():
            time.sleep(0.2)

    except Exception as e:
        logging.exception(f"Unerwarteter Fehler im Hauptprogramm: {e}")
    finally:
        # Shutdown in richtiger Reihenfolge
        if httpd:
            try:
                logging.info("Stoppe HTTP-Server …")
                httpd.shutdown()        # beendet serve_forever()
                httpd.server_close()
            except Exception as e:
                logging.warning(f"HTTP-Server Shutdown-Fehler: {e}")
        if http_thread:
            http_thread.join(timeout=5)

        if mqtt:
            try:
                logging.info("Stoppe MQTT-Client …")
                # vorausgesetzt MqttOrderClient besitzt eine stop()-Methode
                if hasattr(mqtt, "stop"):
                    mqtt.stop()
            except Exception as e:
                logging.warning(f"MQTT-Stop-Fehler: {e}")
        if mqtt_thread:
            mqtt_thread.join(timeout=5)

        logging.info("Alle Dienste beendet.")

if __name__ == "__main__":
    main()
