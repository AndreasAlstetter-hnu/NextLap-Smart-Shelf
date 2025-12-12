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
                 topic_3="ttz-leipheim/state"):
        # Server
        """
        Initialisiert the MQTT-Client with the given parameters.

        :param server_url: URL of the server for HTTP requests
        :param broker: URL of the MQTT broker
        :param port: Port of the MQTT broker
        :param username: Username for the MQTT broker
        :param password: Password for the MQTT broker
        :param topic: MQTT topic for the status updates
        :param topic_2: MQTT topic for the picking orders
        :param topic_3: MQTT topic for the state updates
        :param topic_status: MQTT topic for the status updates
        """
        self.server_url = server_url

        # MQTT
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.topic_2 = topic_2
        self.topic_3 = topic_3

        # Threading for Status Feedback
        self.polling_active = False
        self.poll_interval = 0.1  # Sekunden zwischen Status-Abfragen
        self.poll_thread = None

        # MQTT-Client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()

        self.STATE_TO_ARTICLE = {
            # PLATE
            "Request_Pick_Plate_Lightweight_White": "V_L_WHITE_75",
            "Request_Pick_Plate_Lightweight_Blue":  "V_L_BLUE_75",
            "Request_Pick_Plate_Lightweight_Black": "V_L_BLACK_75",
            "Request_Pick_Plate_Balanced_White":    "V_B_WHITE_75",
            "Request_Pick_Plate_Balanced_Blue":     "V_B_BLUE_75",
            "Request_Pick_Plate_Balanced_Black":    "V_B_BLACK_75",
            "Request_Pick_Plate_Spartan_White":     "V_WHITE_75",
            "Request_Pick_Plate_Spartan_Blue":      "V_BLUE_75",
            "Request_Pick_Plate_Spartan_Black":     "V_BLACK_75",

            # CASE
            "Request_Pick_Case_White":  "V_WHITE_13",
            "Request_Pick_Case_Yellow": "V_YELLOW_13",
            "Request_Pick_Case_Orange": "V_ORANGE_13",
            "Request_Pick_Case_Red":    "V_RED_13",
            "Request_Pick_Case_Green":  "V_GREEN_13",
            "Request_Pick_Case_Blue":   "V_BLUE_13",
            "Request_Pick_Case_Brown":  "V_BROWN_13",
            "Request_Pick_Case_Black":  "V_BLACK_13",

            # BATTERY
            "Request_Pick_Battery": "15",

            # BATTERY CABLE
            "Request_Pick_Battery_Cable": "25",

            # ENGINES
            "Request_Pick_Engine1": "66",
            "Request_Pick_Engine2": "66",
            "Request_Pick_Engine3": "66",
            "Request_Pick_Engine4": "66",

            # RFID TAG
            "Request_Pick_RFID_Tag": "21",

            # RECEIVER
            "Request_Pick_Receiver": "16",

            # RECEIVER CABLE
            "Request_Pick_Receiver_Cable": "24",

            # RIVETS
            "Request_Pick_Rivets": "14",

            # CONTROLLER
            "Request_Pick_Controller": "17",

            # Motoren
            "Request_Pick_Engines":"18"
            
        }

                # Mapping von Request-State auf Response-Topic-Payload
        self.REQUEST_TO_RESPONSE = {
            # PLATE
            "Request_Pick_Plate_Lightweight_White":  "Response_Plate_Picked",
            "Request_Pick_Plate_Lightweight_Blue":   "Response_Plate_Picked",
            "Request_Pick_Plate_Lightweight_Black":  "Response_Plate_Picked",
            "Request_Pick_Plate_Balanced_White":     "Response_Plate_Picked",
            "Request_Pick_Plate_Balanced_Blue":      "Response_Plate_Picked",
            "Request_Pick_Plate_Balanced_Black":     "Response_Plate_Picked",
            "Request_Pick_Plate_Spartan_White":      "Response_Plate_Picked",
            "Request_Pick_Plate_Spartan_Blue":       "Response_Plate_Picked",
            "Request_Pick_Plate_Spartan_Black":      "Response_Plate_Picked",

            # CASE
            "Request_Pick_Case_White":               "Response_Case_Picked",
            "Request_Pick_Case_Yellow":              "Response_Case_Picked",
            "Request_Pick_Case_Orange":              "Response_Case_Picked",
            "Request_Pick_Case_Red":                 "Response_Case_Picked",
            "Request_Pick_Case_Green":               "Response_Case_Picked",
            "Request_Pick_Case_Blue":                "Response_Case_Picked",
            "Request_Pick_Case_Brown":               "Response_Case_Picked",
            "Request_Pick_Case_Black":               "Response_Case_Picked",

            # BATTERY
            "Request_Pick_Battery":                  "Response_Battery_Picked",

            # BATTERY CABLE
            "Request_Pick_Battery_Cable":            "Response_Battery_Cable_Picked",

            # ENGINES 
            "Request_Pick_Engines":                  "Response_Engines_Picked",

            # RFID TAG
            "Request_Pick_RFID_Tag":                 "Response_RFID_Tag_Picked",

            # RECEIVER
            "Request_Pick_Receiver":                 "Response_Receiver_Picked",

            # RECEIVER CABLE
            "Request_Pick_Receiver_Cable":           "Response_Receiver_Cable_Picked",

            # RIVETS
            "Request_Pick_Rivets":                   "Response_Rivets_Picked",

            # CONTROLLER
            "Request_Pick_Controller":               "Response_Controller_Picked"
        }


        # Merkt sich den zuletzt angeforderten Pick-State
        self.last_pick_state = None


        # Callbacks registrieren
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start_status_polling(self):

        """
        Startet das periodische Polling des Auftragsstatus.

        Wenn das Polling bereits aktiv ist, wird nichts unternommen.
        Ansonsten wird ein neuer Thread gestartet, der den Status alle 10 Sekunden abfragt.
        Wenn der Auftrag abgeschlossen ist, wird der Status veröffentlicht.
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
        Periodischer Loop, der den Auftragsstatus von der API abfragt.

        Wenn der Auftrag abgeschlossen ist, wird der Status veröffentlicht und das Polling gestoppt.

        :return: None
        :rtype: None
        """
        while self.polling_active:
            status_data = self.get_server_status()
            if status_data:
                current_status = status_data.get("status")
                logger.debug(f"Aktueller Status vom Server: {current_status}")

                if current_status == "completed":
                    logger.info("✓ Auftrag abgeschlossen!")

                    # Zusätzlich: Response_..._Picked an topic_3 senden
                    if self.last_pick_state:
                        response_name = self.REQUEST_TO_RESPONSE.get(self.last_pick_state)
                        if response_name:
                            try:
                                # Hier nur den Response-Namen als Payload senden
                                payload_resp = response_name
                                # Nur hier veröffentlichen (Status an Nextlap)
                                self.publish_status_to_mqtt(payload_resp)
                            except Exception as e:
                                logger.error(f"Fehler beim Veröffentlichen des Status: {e}")
                        else:
                            logger.warning(
                                f"Kein Response-Mapping für last_pick_state='{self.last_pick_state}' gefunden."
                            )

                        # Nach erfolgreicher/versuchter Rückmeldung State zurücksetzen
                        self.last_pick_state = None

                    # Polling stoppen
                    self.polling_active = False

            time.sleep(self.poll_interval)

    def build_picking_order_from_state(self, state_str: str) -> dict | None:
        """
        Builds a picking order from a given state string.

        :param state_str: The state string to build the order from
        :type state_str: str
        :return: A dictionary containing the picking order data, or None if the state string is unknown
        :rtype: dict | None
        """
        article = self.STATE_TO_ARTICLE.get(state_str)
        if not article:
            logger.warning(f"Unbekannter State für Picking-Order: {state_str}")
            return None

        data = {
            "number": "123456",
            "items": [
                {
                    "number": article
                }
            ]
        }
        return data


    def stop_status_polling(self):
      
        """
        Stops the status polling thread and waits for it to finish.

        :return: None
        :rtype: None
        """
        self.polling_active = False
        if self.poll_thread:
            self.poll_thread.join(timeout=10)
        logger.info("Status-Polling gestoppt.")

    def on_connect(self, client, userdata, flags, rc):
        """
        Called when the client receives a CONNACK response from the server.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or user_data_set()
        :param flags: Response flags sent by the broker
        :param rc: The connection result
        :type client: mqtt.Client
        :type userdata: dict
        :type flags: dict
        :type rc: int
        """
        logger.info(f"Verbunden mit MQTT-Broker, Code: {rc}")
        client.subscribe(self.topic)
        client.subscribe(self.topic_2)
        client.subscribe(self.topic_3)
        logger.info(f"Subscribed to {self.topic} und {self.topic_2}")

    def on_message(self, client, userdata, msg):
        """
        Called when a message is received on a subscribed topic.

        This callback is used to process incoming messages on the 'picking_order' topic (topic_2),
        which contain the order data in JSON format. If the message is not a valid JSON object or
        does not contain the 'number' and 'items' keys, it will be ignored.

        If a message is received on the 'wt_picking' topic (topic), it will be treated as a trigger
        to send a new order to the server.

        If a message is received on the 'state_request' topic (topic_3), it will be used to build a
        picking order for Nextlap. If the state string is not known, the order will be ignored.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or user_data_set()
        :param msg: The message itself
        :type client: mqtt.Client
        :type userdata: dict
        :type msg: mqtt.MQTTMessage
        """
        payload = msg.payload.decode("utf-8-sig").strip()
        payload_clean = payload.replace('\xa0', ' ')
        logger.debug(f"Nachricht empfangen auf {msg.topic}: {payload_clean}")

        # 1) JSON-Aufträge wie bisher (topic_2)
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

        # 2) Alter Trigger (topic)
        elif msg.topic == self.topic and payload_clean == "wt_picking":
            logger.info("Trigger 'wt_picking' erkannt.")
            self.do_server_POST()
            self.start_status_polling()

        # 3) NEU: State-Request auf topic_3 → Picking-Order für Nextlap
        elif msg.topic == self.topic_3:
            logger.info(f"State-Request empfangen: {payload_clean}")

            # Nur echte Request_* States für Picking-Orders verwenden
            if not payload_clean.startswith("Request_"):
                logger.debug(f"Ignoriere Nicht-Request-State auf topic_3: {payload_clean}")
                return

            # Letzten Pick-State merken (nur bei Request_*)
            self.last_pick_state = payload_clean

            data = self.build_picking_order_from_state(payload_clean)
            if data is None:
                logger.warning(f"Keine Zuordnung für State '{payload_clean}' gefunden. Auftrag wird ignoriert.")
                return

            try:
                with open("data.json", "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                logger.debug("Auftrag aus State-Request lokal gespeichert (data.json).")
                self.do_server_POST()
                self.start_status_polling()
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten des State-Auftrags: {e}")

    def do_server_POST(self):
        """
        Sends a POST request to the server to create a new order.

        :return: None
        :rtype: None
        :raises Exception: If there is an error during the request
        """
        try:
            response = requests.post(self.server_url, timeout=5)
            response.raise_for_status()
            logger.info(f"Auftrag erfolgreich erstellt: {response.json()}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Auftrags: {e}")

    def get_server_status(self):

        """
        Abfragt den Status eines Auftrags von der API.

        :return: Ein Dictionary mit dem Status des Auftrags
        :rtype: dict
        :raises Exception: Wenn es einen Fehler bei der Anfrage gibt
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
        Veröffentlicht den Status eines Auftrags an die MQTT-API.

        :param status_data: Ein Dictionary mit dem Status des Auftrags
        :type status_data: dict
        :return: None
        :rtype: None
        :raises Exception: Wenn es einen Fehler bei der Veröffentlichung gibt
        """
        try:
            
            message = json.dumps(status_data, ensure_ascii=False)
            result = self.client.publish(self.topic_3, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Status auf {self.topic_3} veröffentlicht:{status_data}")
            else:
                logger.error(f"Fehler beim Veröffentlichen: {result.rc}")
                
        except Exception as e:
            logger.error(f"Fehler beim Veröffentlichen des Status: {e}")

    def start(self):
        """
        Verbindet den MQTT-Client mit dem Broker und startet den Loop.

        :return: None
        :rtype: None
        """
        logger.info("MQTT-Client verbindet sich…")
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        """
        Stops the MQTT client and disconnects from the broker.

        :return: None
        :rtype: None
        """
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
