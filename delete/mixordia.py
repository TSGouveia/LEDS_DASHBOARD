import requests
import json
import os
from datetime import datetime, timedelta
import yfinance as yf


def print_raw(label, data):
    print(f"\n{'=' * 30}\nDEBUG: {label}\n{'=' * 30}")
    print(json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, (dict, list)) else data)


# --- CONFIG & PERSISTÊNCIA ---
CACHE_FILE = "team_colors.json"
FB_TOKEN = "89a4b73251c44a309c0d5d06c648d461"
FB_HEADERS = {"X-Auth-Token": FB_TOKEN}
MY_TEAM_IDS = [503, 1903, 498, 765]  # Porto, Benfica, Sporting, Portugal


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=4)


TEAM_CACHE = load_cache()


def get_team_color(team_id):
    """Retorna a cor oficial ou cinza. Sem cores aleatórias."""
    t_id = str(team_id)
    if t_id in TEAM_CACHE: return TEAM_CACHE[t_id]

    try:
        res = requests.get(f"https://api.football-data.org/v4/teams/{t_id}", headers=FB_HEADERS, timeout=3).json()
        raw_colors = res.get("clubColors", "Grey")

        # Mapeamento simples de nomes de cores para HEX
        color_map = {
            "Red": "#ff0000",
            "Blue": "#0000ff",
            "Green": "#008000",
            "White": "#ffffff",
            "Black": "#000000",
            "Yellow": "#ffff00"
        }

        primary = raw_colors.split(" / ")[0]
        hex_color = color_map.get(primary, "#888888")

        TEAM_CACHE[t_id] = hex_color
        save_cache(TEAM_CACHE)
        return hex_color
    except:
        return "#888888"


# --- EXECUÇÃO ---

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

# 1. IPMA
weather_data = {}
try:
    url_ipma = "https://api.ipma.pt/public-data/forecast/aggregate/1150322.json"
    r = requests.get(url_ipma, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
    weather_data = r[1]
    print_raw("1. IPMA", weather_data)
except Exception as e:
    print(f"Erro IPMA: {e}")

# 2. MTS
upcoming_mts = []
try:
    url_mts = "https://intranet.mts.pt/api/search"
    payload = {"line": "6", "stations": "19", "day_type": "1", "season": "2"}
    r = requests.post(url_mts, data=payload, timeout=5).json()
    seconds_now = now.hour * 3600 + now.minute * 60 + now.second
    upcoming_mts = [f"{int(t['start_time']) // 3600:02d}:{(int(t['start_time']) % 3600) // 60:02d}"
                    for t in r['data']['times'] if int(t['start_time']) > seconds_now]
    print_raw("2. MTS", upcoming_mts[:5])
except Exception as e:
    print(f"Erro MTS: {e}")

# 3. FOOTBALL
football_games = []
try:
    url_fb = "https://api.football-data.org/v4/matches"
    params_fb = {"dateFrom": today_str, "dateTo": tomorrow_str}
    r_fb = requests.get(url_fb, headers=FB_HEADERS, params=params_fb, timeout=5).json()

    for m in r_fb.get('matches', []):
        if (m['homeTeam']['id'] in MY_TEAM_IDS or m['awayTeam']['id'] in MY_TEAM_IDS) and \
                (m['status'] in ["TIMED", "SCHEDULED", "LIVE", "IN_PLAY"]) and \
                (m['utcDate'].split('T')[0] == today_str):
            football_games.append({
                "status": m['status'],
                "home": m['homeTeam']['tla'],
                "home_color": get_team_color(m['homeTeam']['id']),
                "away": m['awayTeam']['tla'],
                "away_color": get_team_color(m['awayTeam']['id']),
                "score": f"{m['score']['fullTime']['home'] or 0} - {m['score']['fullTime']['away'] or 0}"
            })
    print_raw("3. FOOTBALL", football_games)
except Exception as e:
    print(f"Erro Football: {e}")

# 4. BTC & S&P 500
prices_dict = {"BTC": [], "SP500": []}
try:
    # BTC
    r_btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=eur&days=1",
                         timeout=5).json()
    p_btc = r_btc['prices']
    prices_dict["BTC"] = [p[1] for p in p_btc[::len(p_btc) // 32][:32]]

    # SP500
    sp = yf.Ticker("^GSPC")
    hist = sp.history(period="5d", interval="60m")['Close'].dropna().tolist()
    prices_dict["SP500"] = [round(p, 2) for p in hist[::max(1, len(hist) // 32)][:32]]

    print_raw("4. MARKETS (32 PTS)", prices_dict)
except Exception as e:
    print(f"Erro Mercados: {e}")