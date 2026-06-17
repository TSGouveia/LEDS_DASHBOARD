import time
import threading
import numpy as np
from renderer import LEDRenderer
from fonts import FontLoader
from apps.clock_app import ClockApp
from apps.weather_app import WeatherApp
from apps.mts_app import MTSApp
from apps.football_app import FootballApp
from apps.market_app import MarketApp
from apps.test_app import TestApp
from utils import find_serial_port, update_from_git

# --- CONFIGURAÇÃO DA PLAYLIST ---
PLAYLIST = [
    ("Relógio", 1),
    ("Clima", 1),
    ("Metros", 1),
    ("Futebol", 300),
    ("Mercados", 1),
]

BAUD_RATE = 1000000
UPDATE_CHECK_INTERVAL = 30

def fetch_data_async(app):
    app.is_updating = True
    app.update_data()
    app.is_updating = False

def show_update_screen(renderer, fonts):
    canvas = np.zeros((18, 32, 3), dtype=np.uint8)
    color = (0, 255, 255)
    text = "UPDATING"
    for i, char in enumerate(text):
        fonts.draw_char(canvas, char, i * 4, 7, "3x5", color)
    renderer.display(canvas)
    time.sleep(2)

def main():
    fonts = FontLoader()
    renderer = LEDRenderer(find_serial_port, width=32, height=18, baud=BAUD_RATE)

    available_apps = {
        "Relógio": ClockApp("Relógio", fonts),
        "Clima": WeatherApp("Clima", fonts),
        "Metros": MTSApp("Metros", fonts),
        "Futebol": FootballApp("Futebol", fonts),
        "Mercados": MarketApp("Mercados", fonts),
        "Teste": TestApp("Teste", fonts, duration=40)
    }

    current_playlist_idx = 0
    last_update_check = time.time()

    # Initial load for ALL apps to prevent black screens on skips
    print("[MAIN] Warm-up: Updating all apps...")
    for app in available_apps.values():
        threading.Thread(target=fetch_data_async, args=(app,), daemon=True).start()

    try:
        while True:
            app_name, playlist_duration = PLAYLIST[current_playlist_idx]
            current_app = available_apps[app_name]
            
            # Playlist duration is the master, unless app wants to skip (0)
            if current_app.duration != 0:
                current_app.duration = playlist_duration
            
            actual_duration = current_app.duration
            
            if actual_duration == 0:
                print(f"[MAIN] Skipping {app_name} (duration is 0)")
                current_playlist_idx = (current_playlist_idx + 1) % len(PLAYLIST)
                
                # Start fetch for the app after the one we are skipping to
                next_next_idx = (current_playlist_idx + 1) % len(PLAYLIST)
                next_next_app_name, _ = PLAYLIST[next_next_idx]
                threading.Thread(target=fetch_data_async, args=(available_apps[next_next_app_name],), daemon=True).start()
                continue

            # App is valid, prepare for display
            next_playlist_idx = (current_playlist_idx + 1) % len(PLAYLIST)
            next_app_name, _ = PLAYLIST[next_playlist_idx]
            next_app = available_apps[next_app_name]

            print(f"[MAIN] Exibindo {app_name} por {actual_duration}s")
            start_time = time.monotonic()
            fetch_started = False
            current_app.reset_app(duration=playlist_duration)

            frame_delay = 1.0 / 10
            
            while True:
                loop_start = time.monotonic()
                elapsed = loop_start - start_time
                
                # Desenha e envia para o Renderer (agora em thread segura)
                frame = current_app.draw()
                renderer.display(frame)
                
                # Inicia fetch da PRÓXIMA app 5s antes de acabar o tempo
                if elapsed >= (actual_duration - 5) and not fetch_started:
                    threading.Thread(target=fetch_data_async, args=(next_app,), daemon=True).start()
                    fetch_started = True

                # Verifica Git Update (Executa apenas uma vez por ciclo da app para não pesar)
                if not fetch_started and (time.time() - last_update_check > UPDATE_CHECK_INTERVAL):
                    if update_from_git():
                        show_update_screen(renderer, fonts)
                        return
                    last_update_check = time.time()

                # Controlo de Frame Rate
                processing_time = time.monotonic() - loop_start
                sleep_time = frame_delay - processing_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # SAÍDA DO LOOP: Baseada no tempo real decorrido
                if elapsed >= actual_duration:
                    # Se a próxima app ainda estiver a atualizar, o sistema aguarda no máximo 2s
                    # para não quebrar o ritmo da playlist
                    wait_start = time.monotonic()
                    while next_app.is_updating and (time.monotonic() - wait_start < 2.0):
                        time.sleep(0.1)
                    
                    current_playlist_idx = next_playlist_idx
                    break

    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        renderer.close()

if __name__ == "__main__":
    main()
