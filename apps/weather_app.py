import requests
from .base_app import BaseApp
import numpy as np
import time
from datetime import datetime, timedelta
from dateutil import parser

class WeatherApp(BaseApp):
    def __init__(self, name, font_loader):
        super().__init__(name, font_loader)
        self.data_today = {"temp": "0", "precip": "0", "id": 1}
        self.data_tomorrow = {"temp": "0", "precip": "0", "id": 1}
        self.start_app_time = 0
        self.url = "https://api.ipma.pt/public-data/forecast/aggregate/1150322.json"

    def update_data(self):
        try:
            print(f"\n--- WEATHER SYNC START ---")
            url_agg = "https://api.ipma.pt/public-data/forecast/aggregate/1150322.json"
            url_daily = "https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/1110600.json"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            r_agg = requests.get(url_agg, headers=headers, timeout=10).json()
            r_daily = requests.get(url_daily, headers=headers, timeout=10).json()
            
            now = datetime.now()
            today_date = now.date()
            tomorrow_date = today_date + timedelta(days=1)
            
            # 1. Obter Probabilidade de Precipitação da API Daily (Índices 0 e 1)
            precip_today = "0"
            precip_tomorrow = "0"
            if "data" in r_daily and len(r_daily["data"]) >= 2:
                precip_today = str(int(float(r_daily["data"][0].get("precipitaProb", "0"))))
                precip_tomorrow = str(int(float(r_daily["data"][1].get("precipitaProb", "0"))))
                print(f"Daily API: Hoje={precip_today}%, Amanhã={precip_tomorrow}%")

            def get_best_agg(target_date, target_dt):
                # Filtra entradas do dia alvo
                day_entries = [e for e in r_agg if parser.parse(e['dataPrev']).date() == target_date]
                if not day_entries: return None
                
                # Procura a hora mais próxima (evitando o periodo 24h se houver horários)
                hourly = [e for e in day_entries if int(e.get('idPeriodo', 0)) != 24]
                if hourly:
                    best_e = min(hourly, key=lambda e: abs((parser.parse(e['dataPrev']) - target_dt).total_seconds()))
                else:
                    best_e = day_entries[0]
                
                temp = best_e.get('tMed') or best_e.get('tMax') or "0"
                return {"temp": str(int(float(temp))), "id": int(best_e.get('idTipoTempo', 1))}

            # 2. Obter Temperatura e Ícone da API Aggregate (Hora mais próxima)
            agg_today = get_best_agg(today_date, now)
            agg_tomorrow = get_best_agg(tomorrow_date, now + timedelta(days=1))

            if agg_today:
                self.data_today = {**agg_today, "precip": precip_today}
            if agg_tomorrow:
                self.data_tomorrow = {**agg_tomorrow, "precip": precip_tomorrow}

            print(f"Final: HOJE {self.data_today['temp']}C ({precip_today}%) | AMNH {self.data_tomorrow['temp']}C ({precip_tomorrow}%)")
            print(f"--- WEATHER SYNC END ---\n")
            
            self.start_app_time = time.time()
            self.duration = 10
        except Exception as e:
            print(f"Erro Weather API: {e}")
            self.duration = 0

        except Exception as e:
            print(f"Erro Weather API: {e}")
            self.duration = 0

    def get_weather_icon(self, wid):
        if wid == 1: return "SUN"
        if wid in [2, 3]: return "CLOUDSUN"
        if wid in [4, 5, 16, 17, 24, 25, 26, 27]: return "CLOUD"
        if wid in [6, 7, 9, 10, 12, 13, 15, 18, 28, 29, 30]: return "RAIN"
        if wid in [8, 11, 14, 19, 20, 21, 23]: return "HEAVYRAIN"
        return "SUN"

    def draw_percent(self, canvas, x, y, color):
        canvas[y, x] = color
        canvas[y+1, x+2] = color
        canvas[y+2, x+1] = color
        canvas[y+3, x] = color
        canvas[y+4, x+2] = color

    def get_text_width(self, text):
        return (len(text) * 3) + (len(text) - 1)

    def draw(self):
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        elapsed = time.time() - self.start_app_time
        is_tomorrow = elapsed > 5
        data = self.data_tomorrow if is_tomorrow else self.data_today
        label = "AMNH" if is_tomorrow else "HOJE"
        
        white, blue = (255, 255, 255), (0, 150, 255)
        self.font_loader.draw_bitmap(canvas, self.get_weather_icon(data["id"]), -1, -1, area_w=16, area_h=18)
        t_str = f"{data['temp']}C"
        self.font_loader.draw_text(canvas, t_str, 32 - self.get_text_width(t_str), 1, "3x5", white)
        p_str = data["precip"]
        p_x = 32 - (self.get_text_width(p_str) + 4)
        self.font_loader.draw_text(canvas, p_str, p_x, 7, "3x5", blue)
        self.draw_percent(canvas, 29, 7, blue)
        self.font_loader.draw_text(canvas, label, 32 - self.get_text_width(label), 13, "3x5", (150, 150, 150))
        return canvas
