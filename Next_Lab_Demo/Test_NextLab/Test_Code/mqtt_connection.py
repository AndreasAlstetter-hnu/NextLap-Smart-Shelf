import requests
import paho.mqtt.client as mqtt
import json


class MqttOrderClient:
    def __init__(self,
                 server_url="http://localhost:8310/Drohnen_GmbH",
                 broker="6cb0dc4093f24795858c66688fbff7a0.s1.eu.hivemq.cloud",
                 port=8883,
                 username="mqtt_nextlap",
                 password="F3e9TwAzE5R7",
                 topic="ttz-leipheim/amr",
                 topic_2="ttz-leipheim/picking_order"):
        # Server
        self.server_url = server_url

        # MQTT
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.topic_2 = topic_2


        # MQTT-Client
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()  # TLS aktivieren

        # Callbacks registrieren
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print("Verbunden mit MQTT-Broker, Code:", rc)
        client.subscribe(self.topic)
        client.subscribe(self.topic_2)
        print(f"Subscribed to {self.topic}")
        print(f"Subscribed to {self.topic_2}")

    def on_message(self, client, userdata, msg):

        payload = msg.payload.decode("utf-8-sig").strip()
        payload_clean = payload.replace('\xa0', ' ')
        print(f"Nachricht empfangen auf {msg.topic}: {payload}")

        if msg.topic == self.topic_2 and payload_clean.startswith('{'):
            print("Trigger 'picking_order' erkannt. Verarbeite JSON-Daten...")
            try:
                data = json.loads(payload_clean)
                print(data)
                if "number" in data and "items" in data:
                    print(f"Empfangener Auftrag: {data['number']} mit {len(data['items'])} Artikeln.")
                    with open("data.json", "w", encoding="utf-8") as file:
                        json.dump(data, file, ensure_ascii=False, indent=2)
                    print("Auftrag erfolgreich lokal gespeichert (picking_order.json).")
                    print("Auftrag angekommen. Server POST wird ausgeführt")
                    self.do_server_POST()
                else:
                    print("Fehler: Ungültige JSON-Struktur, erwartete Felder 'number' und 'items' fehlen.")
            except json.JSONDecodeError as err:
                print("Fehler: Ungültiges JSON-Format in empfangenen Daten.")
                print(f"Raw payload: {repr(payload_clean)}")
                print(f"Fehlerdetails: {err}")
            except Exception as e:
                print("Fehler beim Verarbeiten des Auftrags:", e)

            
    
        elif msg.topic == self.topic and payload_clean == "wt_picking":
            print("Trigger 'wt_picking' erkannt. Sende POST an Server...")
            self.do_server_POST()
    

    def do_server_POST(self):

        try:
            response = requests.post(self.server_url, timeout=5)
            response.raise_for_status()
            print("Auftrag erfolgreich erstellt:", response.json())
        except Exception as e:
            print("Fehler beim Erstellen des Auftrags:", e)

    def start(self):
        print("MQTT-Client verbindet sich…")
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        print("MQTT-Client wird gestoppt…")
        self.client.loop_stop()
        self.client.disconnect()
        
if __name__ == "__main__":
    def run_mqtt_client():
        mqtt_client = MqttOrderClient()
        mqtt_client.start()