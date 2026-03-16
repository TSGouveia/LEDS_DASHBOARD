import requests
from .base_app import BaseApp
import numpy as np
import time
from datetime import datetime

class MTSApp(BaseApp):
    def __init__(self, name, font_loader):
        super().__init__(name, font_loader)
        self.upcoming_times = []
        self.url = "https://intranet.mts.pt/api/search"
        self.payload = {"line": "6", "stations": "19", "day_type": "1", "season": "2"}
        self.update_interval = 30  # Metros atualizam rápido

    def update_data(self):
        try:
            now = datetime.now()
            r = requests.post(self.url, data=self.payload, timeout=5).json()
            seconds_now = now.hour * 3600 + now.minute * 60 + now.second
            
            # Filtra tempos futuros
            times = [int(t['start_time']) for t in r['data']['times'] if int(t['start_time']) > seconds_now]
            self.upcoming_times = []
            for t in times[:3]:
                h, m = t // 3600, (t % 3600) // 60
                self.upcoming_times.append(f"{h:02d}:{m:02d}")
            
            # Se não houver tempos, salta o ecrã (duration=0)
            self.duration = 10 if self.upcoming_times else 0
            print(f"MTS Sync: {len(self.upcoming_times)} horários encontrados.")
        except Exception as e:
            print(f"Erro MTS API (Saltando ecrã): {e}")
            self.duration = 0

    def draw_compact_time(self, canvas, time_str, x, y, color):
        curr_x = x
        for i, char in enumerate(time_str):
            if char == ":":
                canvas[y+1, curr_x] = color
                canvas[y+3, curr_x] = color
                curr_x += 2
            else:
                self.font_loader.draw_char(canvas, char, curr_x, y, "3x5", color)
                curr_x += 4

    def draw(self):
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        blue, white = (0, 120, 255), (255, 255, 255)
        self.font_loader.draw_text(canvas, "MTS", 1, 7, "3x5", blue)
        for i, t_str in enumerate(self.upcoming_times):
            self.draw_compact_time(canvas, t_str, 14, 1 + (i * 6), white)
        return canvas
