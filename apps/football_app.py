import requests
from .base_app import BaseApp
import numpy as np
import time
import os
import json
from datetime import datetime, timedelta

# Desativa avisos de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FootballApp(BaseApp):
    def __init__(self, name, font_loader):
        super().__init__(name, font_loader)
        self.games = []
        self.fb_token = "89a4b73251c44a309c0d5d06c648d461"
        self.headers = {"X-Auth-Token": self.fb_token}
        # Adicionado 57 (Arsenal) e 61 (Chelsea) conforme o teu interesse
        self.my_team_ids = [503, 1903, 498, 765]
        self.cache_file = "team_colors.json"
        self.team_cache = self._load_cache()
        self.start_app_time = 0

    def _load_cache(self):
        """Lê o cache do disco."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Guarda o cache no disco."""
        with open(self.cache_file, "w") as f:
            json.dump(self.team_cache, f, indent=4)

    def _hex_to_rgb(self, hex_str):
        try:
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except:
            return (136, 136, 136)

    def get_team_color(self, team_id):
        t_id = str(team_id)
        
        # 1. PRIORIDADE TOTAL: Verifica se já existe no cache (memória ou disco)
        if t_id in self.team_cache:
            return self._hex_to_rgb(self.team_cache[t_id])
        
        # Recarrega do disco (caso tenhas editado o JSON manualmente)
        self.team_cache = self._load_cache()
        if t_id in self.team_cache:
            return self._hex_to_rgb(self.team_cache[t_id])

        # 2. Se não existir, vai buscar à API
        try:
            url = f"https://api.football-data.org/v4/teams/{t_id}"
            res = requests.get(url, headers=self.headers, timeout=5, verify=False).json()
            raw_colors = res.get("clubColors", "Grey / White")
            
            print(f"\n[COLOR API] {res.get('shortName')} ({t_id}): '{raw_colors}'")
            
            keywords = {
                "blue": "#0000ff", "red": "#ff0000", "green": "#00ff00",
                "white": "#ffffff", "yellow": "#ffff00", "gold": "#ffd700",
                "orange": "#ffa500", "purple": "#800080", "claret": "#800000",
                "grey": "#888888", "gray": "#888888"
            }
            
            clean = raw_colors.replace("/", " ").lower()
            chosen_hex = "#888888"
            found = False
            
            # Match inteligente por palavra ou contenção
            words = clean.split()
            for word in words:
                if word in keywords:
                    chosen_hex = keywords[word]
                    found = True; break
            
            if not found:
                for kw, val in keywords.items():
                    if kw in clean:
                        chosen_hex = val
                        found = True; break
            
            # Nunca permitir Black como cor principal
            if chosen_hex == "#000000": chosen_hex = "#888888"

            print(f"[COLOR API] Escolhido: {chosen_hex}")
            self.team_cache[t_id] = chosen_hex
            self._save_cache()
            return self._hex_to_rgb(chosen_hex)
        except Exception as e:
            print(f"[COLOR API] Erro: {e}")
            return (136, 136, 136)

    def update_data(self):
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            temp_games = []
            
            for team_id in self.my_team_ids:
                url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
                params = {"status": "SCHEDULED,LIVE,TIMED,IN_PLAY"}
                response = requests.get(url, headers=self.headers, params=params, timeout=10, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    for m in data.get('matches', []):
                        if m['utcDate'].split('T')[0] == today_str:
                            game_time = m['utcDate'].split('T')[1][:5]
                            score = m.get('score', {}).get('fullTime', {})
                            score_h = score.get('home') if score.get('home') is not None else 0
                            score_a = score.get('away') if score.get('away') is not None else 0
                            
                            game_info = {
                                "home": m['homeTeam']['tla'], "home_id": m['homeTeam']['id'], 
                                "away": m['awayTeam']['tla'], "away_id": m['awayTeam']['id'], 
                                "time": game_time, "status": m['status'],
                                "score_h": str(score_h), "score_a": str(score_a)
                            }
                            if not any(g['time'] == game_time and g['home'] == game_info['home'] for g in temp_games):
                                temp_games.append(game_info)
                time.sleep(0.2)

            temp_games.sort(key=lambda g: 0 if g['status'] in ["LIVE", "IN_PLAY"] else 1)
            self.games = temp_games
            self.duration = 10 * len(self.games) if self.games else 0
            self.start_app_time = time.time()
            print(f"[FOOTBALL] Sync OK. Jogos: {len(self.games)}")
        except Exception as e:
            print(f"[FOOTBALL] Erro Sync: {e}")
            self.duration = 0

    def draw_custom_x(self, canvas, x, y, color):
        canvas[y, x] = color
        canvas[y, x+3] = color
        canvas[y+1, x+1:x+3] = color
        canvas[y+2, x] = color
        canvas[y+2, x+3] = color

    def draw(self):
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        if not self.games: return canvas
        
        elapsed = time.time() - self.start_app_time
        game_idx = int(elapsed // 10)
        if game_idx >= len(self.games): game_idx = len(self.games) - 1
        game = self.games[game_idx]
        
        white, grey = (255, 255, 255), (60, 60, 60)
        c_home = self.get_team_color(game['home_id'])
        c_away = self.get_team_color(game['away_id'])

        if game['status'] in ["LIVE", "IN_PLAY"]:
            self.font_loader.draw_text(canvas, game['home'], 2, 1, "3x5", c_home)
            self.font_loader.draw_text(canvas, game['away'], 19, 1, "3x5", c_away)
            canvas[0:18, 15:17] = white
            self.font_loader.draw_text(canvas, game['score_h'], 5, 8, "5x9", c_home)
            self.font_loader.draw_text(canvas, game['score_a'], 22, 8, "5x9", c_away)
        else:
            self.font_loader.draw_text(canvas, game['home'], 1, 1, "3x5", c_home)
            self.font_loader.draw_text(canvas, game['away'], 20, 1, "3x5", c_away)
            self.draw_custom_x(canvas, 14, 2, grey)
            h_str, m_str = game['time'].split(':')
            self.font_loader.draw_char(canvas, h_str[0], 1, 8, "5x9", white)
            self.font_loader.draw_char(canvas, h_str[1], 7, 8, "5x9", white)
            self.font_loader.draw_char(canvas, m_str[0], 20, 8, "5x9", white)
            self.font_loader.draw_char(canvas, m_str[1], 26, 8, "5x9", white)
            if int(time.time()) % 2 == 0:
                canvas[9:11, 15:17] = white
                canvas[14:16, 15:17] = white
        return canvas
