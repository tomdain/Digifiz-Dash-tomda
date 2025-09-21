import paho.mqtt.client as mqtt
import json

from meite import MEITE
from meite_decoder import MEITEDecoder

# # -------------- Example Usage --------------
# from serial_to_mqtt import SerialToMQTT

# bridge = SerialToMQTT(port="/dev/tty.usbserial-XXXXX")  # change to your serial device
# bridge.start()
# # ------------------------------------------

class SerialToMQTT:
    def __init__(self, port="/dev/ttyUSB0", baud=115200, broker="localhost", mqtt_port=1883, topic_base="me221"):
        self.ecu = MEITE(port=port, baud=baud)
        self.broker = broker
        self.mqtt_port = mqtt_port
        self.topic_base = topic_base

        # Decoder initialisation
        self.decoder = MEITEDecoder()

        # MQTT client setup
        self.client = mqtt.Client(client_id="me221_bridge", protocol=mqtt.MQTTv311)
        self.client.connect(self.broker, self.mqtt_port, 60)
        self.client.loop_start()

    def start(self):
        """Start ECU logging and MQTT publishing"""
        self.ecu.connect()
        self.ecu.start_reporting()
        self.ecu.start_ack_loop()

        try:
            for frame in self.ecu.read_frames():
                parsed = self.ecu.parse_frame(frame)
                self.publish(parsed)
        except KeyboardInterrupt:
            self.stop()

    def publish(self, parsed):
        """Publish ECU data to MQTT"""
        # Always publish raw payload (hex string)
        raw_topic = f"{self.topic_base}/raw"
        self.client.publish(raw_topic, parsed["payload"].hex())

        if parsed["class_id"] == 0:  # Reporting class
            if parsed["msg_id"] == 2:
                # Set State Response → channel definitions
                self.decoder.parse_definition(parsed["payload"])
                self.client.publish(f"{self.topic_base}/definition", parsed["payload"].hex())
                print("[MQTT] Updated channel definitions")

            elif parsed["msg_id"] == 0:
                # Report Response → actual live data
                values = self.decoder.parse_data(parsed["payload"])
                if values:
                    # Publish full JSON
                    decoded_topic = f"{self.topic_base}/decoded"
                    self.client.publish(decoded_topic, json.dumps(values))
                    print(f"[MQTT] Published {decoded_topic} → {values}")

                    # Optionally also publish per-signal topics
                    for name, val in values.items():
                        topic = f"{self.topic_base}/{name}"
                        self.client.publish(topic, val)

    def stop(self):
        """Stop everything cleanly"""
        self.ecu.stop()
        self.client.loop_stop()
        self.client.disconnect()
        print("[SerialToMQTT] Stopped")
