import serial
import struct
import threading
import time

# # -------------- EXAMPLE USAGE --------------
# from meite import MEITE

# ecu = MEITE(port="/dev/tty.usbserial-XXXXX")  # replace with your device
# ecu.connect()
# ecu.start_reporting()
# ecu.start_ack_loop()

# try:
#     for frame in ecu.read_frames():
#         parsed = ecu.parse_frame(frame)
#         print(parsed)
# except KeyboardInterrupt:
#     ecu.stop()
# # -------------------------------------------

class MEITE:
    SYNC = b"ME"

    def __init__(self, port="/dev/ttyUSB0", baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.buffer = b""
        self.running = False

    def connect(self):
        """Open serial connection to ECU"""
        self.ser = serial.Serial(self.port, self.baud, timeout=1)
        print(f"[MEITE] Connected on {self.port} @ {self.baud}")

    def start_reporting(self):
        """Send the request that starts ECU reporting"""
        req = bytes([0x4D, 0x45, 0x01, 0x00,
                     0x00, 0x00, 0x02, 0x01, 0x03, 0x05])
        self.ser.write(req)
        print("[MEITE] Sent start reporting request")

    def start_ack_loop(self):
        """Send ACK every second in a background thread"""
        def loop():
            ack = bytes([0x4D, 0x45, 0x01, 0x00,
                        0x0F, 0x00, 0x01, 0x00, 0x10, 0x3E])  # 7 bytes only
            while self.running:
                self.ser.write(ack)
                print("[MEITE] Sent ACK")
                time.sleep(1)

        self.running = True
        threading.Thread(target=loop, daemon=True).start()
        print("[MEITE] ACK loop started")

    def stop(self):
        """Stop ACK loop and close serial"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[MEITE] Serial closed")

    def read_frames(self):
        """Read from serial and yield complete frames"""
        while self.running:
            data = self.ser.read(1024)
            if data:
                self.buffer += data
                while True:
                    start = self.buffer.find(self.SYNC)
                    if start == -1 or len(self.buffer) < start + 7:
                        break
                    frame_len = struct.unpack_from("<H", self.buffer, start+2)[0]
                    total_len = 7 + frame_len
                    if len(self.buffer) >= start + total_len:
                        frame = self.buffer[start:start+total_len]
                        yield frame
                        self.buffer = self.buffer[start+total_len:]
                    else:
                        break

    def parse_frame(self, frame):
        """Decode and return a frame dict"""
        length = struct.unpack_from("<H", frame, 2)[0]
        msg_type = frame[4]
        class_id = frame[5]
        msg_id = frame[6]
        payload = frame[7:7+length]

        print(f"[MEITE] Frame: len={length}, type={msg_type}, class={class_id}, msg={msg_id}")
        return {
            "len": length,
            "type": msg_type,
            "class_id": class_id,
            "msg_id": msg_id,
            "payload": payload
        }
