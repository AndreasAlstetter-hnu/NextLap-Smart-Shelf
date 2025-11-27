import requests
import paho.mqtt.client as mqtt
import json
import time
import threading
import logging

# -------------------------------------------------
# Logging: alles in server.log, nur INFO+ im Terminal
# -------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File-Handler (DEBUG und höher in server.log)
file_handler = logging.FileHandler("server.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Stream-Handler (nur INFO und höher ins Terminal)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
stream_handler.setFormatter(stream_formatter)

# Handler anhängen (vorher evtl. vorhandene leeren)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class MqttOrderClient:
    def __init__(self,
                 server_url="http://localhost:8310/Drohnen_GmbH",
                 broker="6cb0dc4093f24795858c66688fbff7a0.s1.eu.hivemq.cloud",
                 port=8883,
                 username="mqtt_nextlap",
                 password="F3e9TwAzE5R7",
                 topic="ttz-leipheim/amr",
                 topic_2="ttz-leipheim/picking_order",
                 topic_status="ttz-leipheim/picking_status"):
        # Server
        self.server_url = server_url

        # MQTT
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.topic_2 = topic_2
        self.topic_status = topic_status

        # Threading for Status Feedback
        self.polling_active = False
        self.poll_interval = 0.1  # Sekunden zwischen Status-Abfragen
        self.poll_thread = None

        # MQTT-Client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()

        # Callbacks registrieren
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start_status_polling(self):
        """
        Startet periodisches Polling des Auftragsstatus.
        """
        if self.polling_active:
            logger.debug("Polling läuft bereits.")
            return
        
        self.polling_active = True
        self.poll_thread = threading.Thread(target=self._poll_status_loop, daemon=True)
        self.poll_thread.start()
        logger.info("Status-Polling gestartet.")

    def _poll_status_loop(self):
        """
        Interne Schleife für Status-Polling.
        Veröffentlicht nur, wenn der Auftrag abgeschlossen ist.
        """
        while self.polling_active:
            status_data = self.get_server_status()
            if status_data:
                current_status = status_data.get("status")
                logger.debug(f"Aktueller Status vom Server: {current_status}")

                if current_status == "completed":
                    logger.info("✓ Auftrag abgeschlossen!")
                    # Nur hier veröffentlichen
                    self.publish_status_to_mqtt(status_data)
                    # Polling stoppen
                    self.polling_active = False

            time.sleep(self.poll_interval)

    def stop_status_polling(self):
        """
        Stoppt das periodische Polling.
        """
        self.polling_active = False
        if self.poll_thread:
            self.poll_thread.join(timeout=10)
        logger.info("Status-Polling gestoppt.")

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Verbunden mit MQTT-Broker, Code: {rc}")
        client.subscribe(self.topic)
        client.subscribe(self.topic_2)
        logger.info(f"Subscribed to {self.topic} und {self.topic_2}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8-sig").strip()
        payload_clean = payload.replace('\xa0', ' ')
        logger.debug(f"Nachricht empfangen auf {msg.topic}: {payload_clean}")

        if msg.topic == self.topic_2 and payload_clean.startswith('{'):
            logger.debug("JSON-Nachricht auf 'picking_order' erkannt.")
            try:
                data = json.loads(payload_clean)
                logger.debug(f"Geparste Daten: {data}")
                
                if "number" in data and "items" in data:
                    logger.info(f"Neuer Auftrag empfangen: {data['number']} mit {len(data['items'])} Artikeln.")
                    with open("data.json", "w", encoding="utf-8") as file:
                        json.dump(data, file, ensure_ascii=False, indent=2)
                    logger.debug("Auftrag lokal gespeichert (data.json).")
                    self.do_server_POST()
                    self.start_status_polling()
                else:
                    logger.debug("JSON enthält nicht 'number' und 'items' - ignoriert als Status-Update.")
                    
            except json.JSONDecodeError as err:
                logger.error(f"Ungültiges JSON-Format: {err}")
                logger.debug(f"Raw payload: {repr(payload_clean)}")
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten des Auftrags: {e}")

        elif msg.topic == self.topic and payload_clean == "wt_picking":
            logger.info("Trigger 'wt_picking' erkannt.")
            self.do_server_POST()
            self.start_status_polling()

    def do_server_POST(self):
        try:
            response = requests.post(self.server_url, timeout=5)
            response.raise_for_status()
            logger.info(f"Auftrag erfolgreich erstellt: {response.json()}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Auftrags: {e}")

    def get_server_status(self):
        """
        Fragt den aktuellen Status des zuletzt erstellten Auftrags vom Server ab.
        """
        try:
            response = requests.get(self.server_url, timeout=5)
            response.raise_for_status()
            status_data = response.json()
            logger.debug(f"Auftragsstatus abgerufen: {status_data}")
            return status_data
        except requests.HTTPError as e:
            logger.error(f"HTTP-Fehler beim Abrufen des Status: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.debug(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Auftragsstatus: {e}")
            return None

    def publish_status_to_mqtt(self, status_data):
        """
        Veröffentlicht den Auftragsstatus auf dem MQTT-Topic picking_status.
        """
        try:
            payload = {
                "order_id": status_data.get("id"),
                "order_number": status_data.get("number"),
                "status": status_data.get("status"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            message = json.dumps(payload, ensure_ascii=False)
            result = self.client.publish(self.topic_status, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Status auf {self.topic_status} veröffentlicht: Order {payload['order_number']}")
                logger.debug(f"Vollständige Payload: {payload}")
            else:
                logger.error(f"Fehler beim Veröffentlichen: {result.rc}")
                
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen des Status: {e}")

    def start(self):
        logger.info("MQTT-Client verbindet sich…")
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        logger.info("MQTT-Client wird gestoppt…")
        self.client.loop_stop()
        self.client.disconnect()

        
if __name__ == "__main__":
    mqtt_client = MqttOrderClient()
    mqtt_client.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Programm wird beendet...")
        mqtt_client.stop()
