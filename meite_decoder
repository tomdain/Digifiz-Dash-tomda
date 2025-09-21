import struct

# Data ID → name mapping (from Appendix A of doc)
CHANNEL_NAMES = {
    1: "RPM",
    2: "Sync Status",
    3: "Lost Sync Count",
    4: "Injector Duty - %",
    5: "MAP Raw",
    6: "MAP – KPa",
    7: "TPS Raw",
    8: "TPS - %",
    9: "Primary Load - %",
    10: "Secondary Load - %",
    11: "O2 Raw",
    12: "O2 Val – Volts",
    13: "Coolant Temp. Raw",
    14: "Coolant Temp. – Deg. Celsius",
    15: "Intake Air Temp Raw",
    16: "Intake Air Temp – Deg. Celsius",
    17: "Battery Voltage Raw",
    18: "Batter Voltage – Volts",
    19: "Acceleration Enrichment Delta",
    20: "[Not used] Idle RPM Error",
    21: "Airflow Est. – grams/sec",
    22: "Fuelflow Est. – Litres/Hr",
    23: "Base Table Dwell – ms",
    24: "Ignition Advance Pri. – Deg",
    25: "Ignition Adv. Sec. – Deg",
    26: "Ignition Adv. Knock Mod – Trim",
    27: "Ignition Coolant Mod – Trim",
    28: "Ignition Intake Air. Temp Mod – Trim",
    29: "Ignition Adv. Secondary Load Mod – Trim",
    30: "Ignition Adv. RPM Limiter Adder – Deg C",
    31: "Ignition Adv. ALS Limiter Adder – Deg C",
    32: "Current Target AFR – AFR",
    33: "Base VE - %",
    34: "Sec. VE - %",
    35: "Acceleration Enrichment VE Adder - %",
    36: "Total VE - %",
    37: "Base Pulse-Width – ms",
    38: "Inj. Coolant Mod – Trim",
    39: "Inj. Intake Air Temp. Mod – Trim",
    40: "Inj. Idle PWM Duty Mod – Trim",
    41: "Inj. Secondary Load Mod – Trim",
    42: "Inj. Knock Mod – Trim",
    43: "Inj. Cranking Mod – Trim",
    44: "Inj. After-Start Enrichment Mod – Trim",
    45: "Inj. RPM Limiter Mod – Trim",
    46: "Inj. Lambda Mod – Trim",
    47: "Inj. Overrun Mod – Trim",
    48: "Inj. Dead Time – ms",
    49: "After-start Decay Time Left – seconds",
    50: "Acceleration Enrichment Trim",
    51: "Acceleration Enrichment Last Trigger Delta",
    52: "Acc. Enrichment Coolant Trim",
    53: "Acc. Enrichment MAP Delta",
    54: "Acc. Enrichment TPS Delta",
    55: "Current RPM Limiter",
    56: "Idle Table PWM Duty - %",
    57: "Idle Target RPM",
    58: "Idle Status",
    59: "Idle PWM Duty - %",
    60: "Idle Closed Loop P Component",
    61: "Idle Closed Loop I Component",
    62: "Idle Closed Loop D Component",
    63: "Idle Target RPM Error",
    64: "Knock Acceptable Level Final",
    65: "Knock Sensor Value",
    66: "Knock Status",
    67: "Knock Cylinder 1 Window Start – Deg",
    68: "Boost Target MAP – KPa",
    69: "Boost Status",
    70: "Boost Final PWM Duty - %",
    71: "Boost Closed Loop P Comp",
    72: "Boost Closed Loop I Comp",
    73: "Boost Closed Loop D Comp",
    74: "Boost Target MAP Error – KPa",
    75: "Alternator Status",
    76: "Alternator Ctrl. Duty - %",
    77: "Lambda Current AFR",
    78: "Lambda AFR Error",
    79: "Lambda Long Term Trim – Trim",
    80: "Lambda Status",
    81: "Long Term Trim Status",
    82: "Long Term Trim Confidence Level – %",
    83: "Long Term Trim Store Timer Sec. – seconds",
    84: "AC Status",
    85: "Vehicle Speed",
    86: "Current gear",
    87: "Calculated vehicle speed",
    88: "Overrun Status",
    89: "VICS Status",
    90: "Purge Valve Status",
    91: "Launch Control Status",
    92: "ALS Status",
    93: "LC/ALS Switch Status",
    94: "VVT Status",
    95: "VVT PWM Duty – %",
    96: "Cam Current Advance – Deg",
    97: "Cam Target Advance – Deg",
    98: "VVT P Component",
    99: "VVT I Component",
    100: "Selected Map Boost",
    101: "Selected Map Ignition",
    102: "Selected Map Injection",
    103: "Datalogging Status",
    104: "Datalogging Time Left Seconds",
    105: "Final Ignition Advance Angle – Deg",
    106: "Final Ignition Dwell – ms",
    107: "Final Injection Angle – deg",
    108: "Final Injection Pulse Width – ms",
    109: "Number of crank IRQs",
    110: "Number of cam IRQs"
}

# Type code → struct format
TYPE_MAP = {
    0: "<f",  # float32
    1: "<h",  # int16
    2: "<H",  # uint16
    3: "<b",  # int8
    4: "<B",  # uint8
    5: "<?",  # bool
}

class MEITEDecoder:
    def __init__(self):
        self.channel_map = []  # [(name, fmt), ...]

    def parse_definition(self, payload: bytes):
        """Decode msg=2 payload (channel definitions)."""
        status = payload[0]
        num_entities = struct.unpack_from("<H", payload, 1)[0]
        offset = 3
        self.channel_map = []

        for _ in range(num_entities):
            data_id = struct.unpack_from("<H", payload, offset)[0]
            dtype = payload[offset+2]
            offset += 3

            name = CHANNEL_NAMES.get(data_id, f"chan_{data_id}")
            fmt = TYPE_MAP.get(dtype)
            if fmt:
                self.channel_map.append((name, fmt))

        print("[MEITE] Channel map built:", self.channel_map)

    def parse_data(self, payload: bytes):
        """Decode msg=0 payload (live values)."""
        if not self.channel_map:
            print("[MEITE] No channel map yet, skipping data")
            return {}

        status = payload[0]
        offset = 1
        values = {}

        for name, fmt in self.channel_map:
            size = struct.calcsize(fmt)
            raw = payload[offset:offset+size]
            if len(raw) == size:
                val = struct.unpack(fmt, raw)[0]
                values[name] = val
            offset += size

        return values
