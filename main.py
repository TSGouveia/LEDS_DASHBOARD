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
from utils import find_serial_port, update_from_git

# --- CONFIGURAÇÃO DA PLAYLIST ---
# Podes escolher quais apps aparecem e durante quanto tempo (em segundos)
# Exemplo: Relógio (300s = 5m), Clima (20s), Futebol (45s)
PLAYLIST = [
    ("Relógio", 2),
    ("Clima", 60),
    ("Metros", 60),
    #("Futebol", 60),
    ("Mercados", 60),
]

BAUD_RATE = 1000000
UPDATE_CHECK_INTERVAL = 30  # Verificação do Git a cada 30 segundos

def fetch_data_async(app):
    app.is_updating = True
    app.update_data()
    app.is_updating = False

def show_update_screen(renderer, fonts):
    """Desenha um ecrã de 'UPDATING' nos LEDs antes de reiniciar."""
    canvas = np.zeros((18, 32, 3), dtype=np.uint8)
    color = (0, 255, 255) # Ciano
    text = "UPDATING"
    for i, char in enumerate(text):
        fonts.draw_char(canvas, char, i * 4, 7, "3x5", color)
    renderer.display(canvas)
    time.sleep(2)

def main():
    fonts = FontLoader()
    renderer = LEDRenderer(find_serial_port, width=32, height=18, baud=BAUD_RATE)

    # Inicializamos todas as apps disponíveis
    available_apps = {
        "Relógio": ClockApp("Relógio", fonts),
        "Clima": WeatherApp("Clima", fonts),
        "Metros": MTSApp("Metros", fonts),
        "Futebol": FootballApp("Futebol", fonts),
        "Mercados": MarketApp("Mercados", fonts)
    }

    current_playlist_idx = 0
    last_update_check = time.time()

    # Carregamento inicial da primeira app da playlist
    first_app_name, _ = PLAYLIST[current_playlist_idx]
    current_app = available_apps[first_app_name]
    current_app.update_data()

    try:
        while True:
            # 1. Configura a app atual da playlist
            app_name, duration = PLAYLIST[current_playlist_idx]
            current_app = available_apps[app_name]
            
            # 2. Configura a próxima app para o fetch em background
            next_playlist_idx = (current_playlist_idx + 1) % len(PLAYLIST)
            next_app_name, _ = PLAYLIST[next_playlist_idx]
            next_app = available_apps[next_app_name]

            print(f"[MAIN] Exibindo {app_name} por {duration}s")
            start_time = time.time()
            fetch_started = False
            current_app.reset_app()

            # Loop de exibição da app atual
            while True:
                frame = current_app.draw()
                renderer.display(frame)
                time.sleep(0.1)

                elapsed = time.time() - start_time

                # Inicia o fetch da próxima app 5 segundos antes de trocar ou assim que possível
                if elapsed >= (duration - 5) and not fetch_started:
                    threading.Thread(target=fetch_data_async, args=(next_app,), daemon=True).start()
                    fetch_started = True

                # Verificação periódica do Git
                if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
                    if update_from_git():
                        show_update_screen(renderer, fonts)
                        return
                    last_update_check = time.time()

                # Troca de app quando o tempo acaba E o fetch da próxima terminou
                if elapsed >= duration:
                    if not next_app.is_updating:
                        current_playlist_idx = next_playlist_idx
                        break
                    else:
                        # Se a próxima ainda estiver a atualizar, espera mais um pouco
                        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        renderer.close()

if __name__ == "__main__":
    main()
