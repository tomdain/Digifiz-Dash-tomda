import paho.mqtt.client as mqtt
import json

from meite import MEITE
from meite_decoder import MEITEDecoder

# # -------------- Example Usage --------------
# from serial_to_mqtt import SerialToMQTT

# bridge = SerialToMQTT(port="/dev/tty.usbserial-XXXXX")  # change to your serial device
# bridge.start()
# # ------------------------------------------

CHANNEL_TO_TOPIC = {
    "RPM": "engine/rpm/state",
    "Coolant Temp. – Deg. Celsius": "engine/coolant/state",
    "MAP – KPa": "engine/boost/state",
    "Batter Voltage – Volts": "engine/fuel/state",
    "Injector Duty - %": "engine/injector_duty/state",
    "O2 Val – Volts": "engine/o2/state",
    "TPS - %": "engine/tps/state",
    "Vehicle Speed": "cabin/speed_cv/state",
    # you can add more as needed
}

# client.message_callback_add('engine/egt/state', on_message_egt)
# client.message_callback_add('engine/oilpressure/state', on_message_oilpressure)
# client.message_callback_add('engine/fuel/state', on_message_fuel)
# client.message_callback_add('cabin/outside_temp/state', on_message_outside_temp)
# client.message_callback_add('cabin/speed_cv/state', on_message_speed_cv)
# client.message_callback_add('indicator/illumination/state', on_message_illumination)
# client.message_callback_add('indicator/foglight/state', on_message_foglight)
# client.message_callback_add('indicator/defog/state', on_message_defog)
# client.message_callback_add('indicator/highbeam/state', on_message_highbeam)
# client.message_callback_add('indicator/leftturn/state', on_message_leftturn)
# client.message_callback_add('indicator/rightturn/state', on_message_rightturn)
# client.message_callback_add('indicator/brakewarn/state', on_message_brakewarn)
# client.message_callback_add('indicator/oillight/state', on_message_oillight)
# client.message_callback_add('indicator/alt/state', on_message_alt)
# client.message_callback_add('indicator/glow/state', on_message_glow)

class SerialToMQTT:
    def __init__(self, client, port="/dev/ttyUSB0", baud=115200, broker="localhost", mqtt_port=1883, topic_base="me221"):
        self.ecu = MEITE(port=port, baud=baud)
        self.broker = broker
        self.mqtt_port = mqtt_port
        self.topic_base = topic_base

        # Decoder initialisation
        self.decoder = MEITEDecoder()

        # MQTT client setup
        self.client = client  # Use the client passed in
        self.running = False
        # self.client = mqtt.Client(client_id="me221_bridge", protocol=mqtt.MQTTv311)
        # self.client.connect(self.broker, self.mqtt_port, 60)
        # self.client.loop_start()

    def start(self):
        """Start ECU logging and MQTT publishing"""
        self.running = True
        self.ecu.connect()
        self.ecu.start_reporting()
        self.ecu.start_ack_loop()

        try:
            for frame in self.ecu.read_frames():
                if not self.running:
                    break
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
                    # print(f"[MQTT] Published {decoded_topic} → {values}")

                    # Publish only mapped signals to dash topics
                    for channel_name, topic in CHANNEL_TO_TOPIC.items():
                        if channel_name in values:
                            val = values[channel_name]
                            self.client.publish(topic, val)
                            print(f"[MQTT] Published {topic} → {val}")

    def stop(self):
        """Stop everything cleanly"""
        self.ecu.stop()
        self.running = False
        # self.client.loop_stop()
        # self.client.disconnect()
        print("[SerialToMQTT] Stopped")
