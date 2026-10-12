import os
import random
import threading
import time

# Simulated DC fast-charging session, the same data a real charging station shows on its screen.
# The station has a single connector, so there is one session shared by every page of the website.

STATION = {
    "name": "NOI Techpark",
    "address": "Via Alessandro Volta 13A, Bolzano",
    "charger_id": "HPC-03",
    "connector": "CCS2",
    "max_power_kw": 150,
}
PRICE_PER_KWH = float(os.getenv('CHARGING_PRICE_PER_KWH', '0.59'))
# Speeds up the simulation for demos (1 = real time)
TIME_SCALE = float(os.getenv('CHARGING_TIME_SCALE', '1'))

BATTERY_KWH = 77.0
CONSUMPTION_KWH_PER_KM = 0.17
TARGET_SOC = 80.0
PREPARING_SECONDS = 12  # authorization, cable check and precharge before the power ramps up
SAMPLE_EVERY = 15       # seconds of charging between two points of the power chart


def vehicle_power_kw(soc):
    # Typical charging curve of an 800V-ready mid-size EV: a short ramp, a plateau, then the taper
    if soc < 10:
        power = 110 + 2.5 * soc
    elif soc < 35:
        power = 135
    elif soc < 55:
        power = 135 - (soc - 35) * 1.75
    elif soc < 80:
        power = 100 - (soc - 55) * 1.8
    else:
        power = 55 - (soc - 80) * 2.2
    return max(4.0, min(power, STATION["max_power_kw"]))


def pack_voltage(soc):
    return 355 + soc * 0.6


def seconds_to_target(soc, target):
    seconds = 0
    while soc < target:
        soc += vehicle_power_kw(soc) * 10 / 3600 / BATTERY_KWH * 100
        seconds += 10
    return seconds


class ChargingSession:
    def __init__(self):
        self.lock = threading.Lock()
        self.start()

    def start(self):
        self.started_at = time.time()
        self.last_update = self.started_at
        self.status = "preparing"
        self.soc = round(random.uniform(14, 32), 1)
        self.start_soc = self.soc
        self.energy_kwh = 0.0
        self.power_kw = 0.0
        self.elapsed = 0.0          # simulated seconds since the plug-in
        self.charging_time = 0.0    # simulated seconds with power flowing
        self.battery_temp = round(random.uniform(21, 25), 1)
        self.history = []
        self.ended_at = None

    def _step(self, dt):
        self.elapsed += dt
        if self.status == "preparing":
            if self.elapsed >= PREPARING_SECONDS:
                self.status = "charging"
            return

        self.charging_time += dt
        # The power ramps up during the first seconds, like on a real charger
        ramp = min(1.0, self.charging_time / 20)
        self.power_kw = vehicle_power_kw(self.soc) * ramp * random.uniform(0.985, 1.015)
        energy = self.power_kw * dt / 3600
        self.energy_kwh += energy
        self.soc = min(100.0, self.soc + energy / BATTERY_KWH * 100)
        # The pack warms up under high power and cools down slowly
        target_temp = 24 + self.power_kw / 9
        self.battery_temp += (target_temp - self.battery_temp) * dt / 600

        if self.charging_time // SAMPLE_EVERY > len(self.history) - 1:
            self.history.append({"t": round(self.elapsed / TIME_SCALE), "power": round(self.power_kw, 1), "soc": round(self.soc, 1)})
            self.history = self.history[-240:]

        if self.soc >= TARGET_SOC:
            self._end("complete")

    def _end(self, status):
        self.status = status
        self.power_kw = 0.0
        self.ended_at = time.time()

    def _advance(self):
        now = time.time()
        dt = (now - self.last_update) * TIME_SCALE
        self.last_update = now
        while dt > 0 and self.status in ("preparing", "charging"):
            step = min(1.0, dt)
            self._step(step)
            dt -= step

    def stop(self):
        with self.lock:
            self._advance()
            if self.status in ("preparing", "charging"):
                self._end("stopped")

    def restart(self):
        with self.lock:
            self.start()

    def snapshot(self):
        with self.lock:
            self._advance()
            active = self.status in ("preparing", "charging")
            remaining = seconds_to_target(self.soc, TARGET_SOC) / TIME_SCALE if active else 0
            voltage = pack_voltage(self.soc) if self.status == "charging" else 0.0
            return {
                "station": STATION,
                "status": self.status,
                "soc": round(self.soc, 1),
                "start_soc": self.start_soc,
                "target_soc": TARGET_SOC,
                "power_kw": round(self.power_kw, 1),
                "voltage_v": round(voltage),
                "current_a": round(self.power_kw * 1000 / voltage) if voltage else 0,
                "energy_kwh": round(self.energy_kwh, 2),
                "cost": round(self.energy_kwh * PRICE_PER_KWH, 2),
                "price_per_kwh": PRICE_PER_KWH,
                "range_added_km": round(self.energy_kwh / CONSUMPTION_KWH_PER_KM),
                "battery_temp_c": round(self.battery_temp, 1),
                "elapsed_s": round(self.elapsed / TIME_SCALE),
                "remaining_s": round(remaining),
                "history": self.history,
            }

    def bot_context(self):
        # A short description of the session, so the bot suggests activities that fit the remaining time
        data = self.snapshot()
        if data["status"] in ("preparing", "charging"):
            minutes = max(1, round(data["remaining_s"] / 60))
            return f"The vehicle is at {data['soc']:.0f}% battery and needs about {minutes} more minute{'s' if minutes > 1 else ''} to reach {data['target_soc']:.0f}%."
        return "The vehicle has finished charging, so the user can leave whenever they want."


charging_session = ChargingSession()
