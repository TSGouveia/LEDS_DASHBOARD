import requests
from .base_app import BaseApp
import numpy as np
import time
import os
import json
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# Desativa avisos de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FootballApp(BaseApp):
    # --- CONFIGURAÇÃO FÁCIL PARA DEBUG ---
    LOOKAHEAD_HOURS = 24  # Altera aqui para ex: 72 ou 168 (1 semana) para testar
    MY_TEAM_IDS = [503, 1903, 498, 765,1777] # Porto, Benfica, Sporting, Portugal
    # -------------------------------------

    def __init__(self, name, font_loader):
        super().__init__(name, font_loader)
        self.games = []
        self.last_update_time = 0
        self.fb_token = "89a4b73251c44a309c0d5d06c648d461"
        self.cache_file = "team_colors.json"
        self.team_cache = self._load_cache()
        # Pre-convert hex to RGB for fast drawing
        self.rgb_cache = {str(k): self._hex_to_rgb(v) for k, v in self.team_cache.items()}
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": self.fb_token})
        self.start_app_time = 0

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[FOOTBALL] Error loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.team_cache, f, indent=4)
        except Exception as e:
            print(f"[FOOTBALL] Error saving cache: {e}")

    def _hex_to_rgb(self, hex_str):
        try:
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except:
            return (136, 136, 136)

    def get_team_color(self, team_id):
        t_id = str(team_id)
        return self.rgb_cache.get(t_id, (136, 136, 136))

    def _ensure_team_color(self, team_id):
        """Fetches team color from API if not in cache."""
        t_id = str(team_id)
        if t_id in self.rgb_cache:
            return

        try:
            url = f"https://api.football-data.org/v4/teams/{t_id}"
            res = self.session.get(url, timeout=5, verify=False).json()
            raw_colors = res.get("clubColors", "Grey / White")
            
            # Mapeamento expandido de cores
            keywords = {
                "blue": "#0000ff", "red": "#ff0000", "green": "#00ff00",
                "white": "#ffffff", "yellow": "#ffff00", "gold": "#ffd700",
                "orange": "#ffa500", "purple": "#800080", "claret": "#800000",
                "grey": "#888888", "gray": "#888888", "navy": "#000080",
                "maroon": "#800000", "sky": "#87ceeb"
            }
            
            clean_parts = [p.strip().lower() for p in raw_colors.replace("/", " ").split()]
            chosen_hex = "#888888" # Default grey
            for part in clean_parts:
                if part in keywords:
                    chosen_hex = keywords[part]
                    break
                for kw, val in keywords.items():
                    if kw in part:
                        chosen_hex = val
                        break
                if chosen_hex != "#888888": break

            if chosen_hex == "#000000": chosen_hex = "#888888"
            
            if chosen_hex != "#888888":
                self.team_cache[t_id] = chosen_hex
                self.rgb_cache[t_id] = self._hex_to_rgb(chosen_hex)
                self._save_cache()
                print(f"[FOOTBALL] Cached color for team {t_id} ({raw_colors}): {chosen_hex}")
            else:
                self.rgb_cache[t_id] = (136, 136, 136)
                print(f"[FOOTBALL] No valid color found for team {t_id} ({raw_colors}). Using temporary grey.")
        except Exception as e:
            print(f"[FOOTBALL] Error fetching color for team {t_id}: {e}")
            self.rgb_cache[t_id] = (136, 136, 136)

    def _fetch_team_matches(self, team_id, date_from, date_to):
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
        params = {"dateFrom": date_from, "dateTo": date_to}
        try:
            resp = self.session.get(url, params=params, timeout=8, verify=False)
            if resp.status_code == 200:
                return resp.json().get('matches', [])
            elif resp.status_code == 429:
                print(f"[FOOTBALL] Rate limit (429) for team {team_id}")
        except Exception as e:
            print(f"[FOOTBALL] Error fetching matches for team {team_id}: {e}")
        return []

    def update_data(self):
        """Updates matches for the configured lookahead window with timezone conversion."""
        now_ts = time.time()
        throttle = 120 if self.games else 600
        if now_ts - self.last_update_time < throttle and self.last_update_time != 0:
            print("[FOOTBALL] Skipping update (throttled)")
            return

        try:
            # Use timezone-aware local time
            now = datetime.now().astimezone()
            limit_dt = now + timedelta(hours=self.LOOKAHEAD_HOURS)
            today_str = now.strftime("%Y-%m-%d")
            limit_str = limit_dt.strftime("%Y-%m-%d")
            
            print(f"[FOOTBALL] Fetching matches from {today_str} to {limit_str} (Lookahead: {self.LOOKAHEAD_HOURS}h)...")
            
            all_matches = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(self._fetch_team_matches, tid, today_str, limit_str) for tid in self.MY_TEAM_IDS]
                for f in futures:
                    all_matches.extend(f.result())

            seen_ids = set()
            temp_games = []
            for m in all_matches:
                if m['id'] in seen_ids: continue
                seen_ids.add(m['id'])
                utc_dt = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                local_dt = utc_dt.astimezone()
                if m['status'] == "FINISHED" or local_dt > limit_dt:
                    continue

                score = m.get('score', {}).get('fullTime', {})
                game_info = {
                    "home": m['homeTeam']['tla'], "home_id": m['homeTeam']['id'],
                    "away": m['awayTeam']['tla'], "away_id": m['awayTeam']['id'],
                    "time": local_dt.strftime("%H:%M"),
                    "status": m['status'],
                    "score_h": str(score.get('home') if score.get('home') is not None else 0),
                    "score_a": str(score.get('away') if score.get('away') is not None else 0),
                    "match_id": m['id'],
                    "dt": local_dt
                }
                temp_games.append(game_info)
                self._ensure_team_color(m['homeTeam']['id'])
                self._ensure_team_color(m['awayTeam']['id'])

            temp_games.sort(key=lambda g: (0 if g['status'] in ["LIVE", "IN_PLAY"] else 1, g['dt']))
            self.games = temp_games

            # --- DEBUG: INJETAR JOGO FAKE LIVE ---
            fake_game = {
                "home": "FKE", "home_id": "9999",
                "away": "TST", "away_id": "8888",
                "time": "00:00",
                "status": "LIVE",
                "score_h": "3", "score_a": "1",
                "match_id": 0,
                "dt": now
            }
            self.games.insert(0, fake_game)
            self.rgb_cache["9999"] = (200, 0, 0)
            self.rgb_cache["8888"] = (0, 0, 200)
            # -------------------------------------
            
            self.last_update_time = now_ts
            # Only set to 0 if we want to skip. Else, leave it so main.py can set it.
            if not self.games:
                self.duration = 0
            print(f"[FOOTBALL] Update OK. {len(self.games)} games found (1 FAKE LIVE).")
        except Exception as e:
            print(f"[FOOTBALL] General update error: {e}")
            self.duration = 0

    def reset_app(self, duration=None):
        super().reset_app(duration)
        self.start_app_time = time.time()

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
        # Divide total duration equally among all games
        per_game_time = self.duration / len(self.games)
        game_idx = int(elapsed // per_game_time) % len(self.games)
        game = self.games[game_idx]
        
        white, grey = (255, 255, 255), (60, 60, 60)
        c_home = self.get_team_color(game['home_id'])
        c_away = self.get_team_color(game['away_id'])

        if game['status'] in ["LIVE", "IN_PLAY"]:
            # LIVE UI: Colored backgrounds
            canvas[:, 0:16] = c_home
            canvas[:, 16:32] = c_away
            # White text on colors
            self.font_loader.draw_text(canvas, game['home'], 2, 1, "3x5", white)
            self.font_loader.draw_text(canvas, game['away'], 19, 1, "3x5", white)
            canvas[0:18, 15:17] = white
            self.font_loader.draw_text(canvas, game['score_h'], 5, 8, "5x9", white)
            self.font_loader.draw_text(canvas, game['score_a'], 22, 8, "5x9", white)
        else:
            # SCHEDULED UI: Black background, Team colors as text
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
