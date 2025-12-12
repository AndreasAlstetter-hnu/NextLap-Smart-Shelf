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
    """
    Returns the port number to use for the HTTP server.

    The port can be specified in three ways, in the following order of priority:

    1. Environment variable NEXTLAB_PORT
    2. Command line argument (first argument)
    3. Default value (8310)

    :return: The port number to use
    :rtype: int
    """
    if "NEXTLAB_PORT" in os.environ:
        return int(os.environ["NEXTLAB_PORT"])
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    return default

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True  # schnelleres Rebind bei Neustarts

def start_http_server(port: int):
    """
    Starts an HTTP server on the given port.

    The server will be started in a separate thread and will be configured to
    reuse the address in case of a bind error.

    :param port: The port number to use for the HTTP server
    :type port: int
    :return: A tuple containing the started HTTP server and the thread it's running in
    :rtype: tuple[http.server.HTTPServer, threading.Thread]
    """
    httpd = ReusableHTTPServer(("0.0.0.0", port), PickingAdapterHandler)
    t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.5}, name="http-server", daemon=False)
    t.start()
    logging.info(f"HTTP-Server gestartet auf Port {port} (Thread {t.name})")
    return httpd, t

def start_mqtt_client():
    
    """
    Starts an MQTT client in a separate thread.

    The client will be started in a separate thread and will be configured to
    connect to the MQTT broker and subscribe to the picking topic.

    :return: A tuple containing the started MQTT client and the thread it's running in
    :rtype: tuple[mqtt_connection.MqttOrderClient, threading.Thread]
    """
    client = MqttOrderClient()
    t = threading.Thread(target=client.start, name="mqtt-client", daemon=False)  # client.start() blockiert, bis stop()
    t.start()
    logging.info(f"MQTT-Client gestartet (Thread {t.name})")
    return client, t

def main():
    """
    Hauptprogramm der Anwendung

    Führt eine HTTP-API auf einem lokalen Server auf, die
    Aufträge von NextLab an die lokale API weiterleitet.

    Außerdem wird ein MQTT-Client gestartet, der
    Aufträge an die lokale API sendet und Status-Updates
    von der API empfängt.

    Der Dienst wird durch STRG+C (SIGINT) oder Stop-BAT
    (SIGTERM) beendet.

    :return: None
    :rtype: None
    """
    port = get_port()
    stop_evt = threading.Event()

    def on_signal(sig, frame):
        """
        Signal handler for SIGINT and SIGTERM.

        Called when either SIGINT (STRG+C) or SIGTERM (Stop-BAT) is received.

        :param sig: The signal that was received
        :type sig: int
        :param frame: The current stack frame
        :type frame: frame
        :return: None
        :rtype: None
        """
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
