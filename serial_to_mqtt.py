import paho.mqtt.client as mqtt
from meite import MEITE

# # -------------- Example Usage --------------
# from serial_to_mqtt import SerialToMQTT

# bridge = SerialToMQTT(port="/dev/tty.usbserial-XXXXX")  # change to your serial device
# bridge.start()
# # ------------------------------------------

class SerialToMQTT:
    def __init__(self, port="/dev/ttyUSB0", broker="localhost", mqtt_port=1883, topic_base="me221"):
        self.ecu = MEITE(port=port)
        self.broker = broker
        self.mqtt_port = mqtt_port
        self.topic_base = topic_base

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
        topic = f"{self.topic_base}/raw"
        self.client.publish(topic, parsed["payload"].hex())
        print(f"[MQTT] Published {topic} → {parsed['payload'].hex()}")

        # Example expansion: publish by msg_id
        if parsed["class_id"] == 0:  # REPORT class
            if parsed["msg_id"] == 0:
                self.client.publish(f"{self.topic_base}/report", parsed["payload"].hex())
            elif parsed["msg_id"] == 2:
                self.client.publish(f"{self.topic_base}/set_state", parsed["payload"].hex())

    def stop(self):
        """Stop everything cleanly"""
        self.ecu.stop()
        self.client.loop_stop()
        self.client.disconnect()
        print("[SerialToMQTT] Stopped")
