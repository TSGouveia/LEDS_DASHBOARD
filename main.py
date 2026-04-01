import time
import threading
from renderer import LEDRenderer
from fonts import FontLoader
from apps.clock_app import ClockApp
from apps.weather_app import WeatherApp
from apps.mts_app import MTSApp
from apps.football_app import FootballApp
from apps.market_app import MarketApp
from utils import find_serial_port, update_from_git

# --- CONFIGURAÇÃO ---
BAUD_RATE = 1000000
UPDATE_CHECK_INTERVAL = 600 # 10 minutos em segundos

def fetch_data_async(app):
    app.is_updating = True
    app.update_data()
    app.is_updating = False

def main():
    fonts = FontLoader()
    # Passamos a função find_serial_port em vez de uma porta fixa para o renderer ser resiliente
    renderer = LEDRenderer(find_serial_port, width=32, height=18, baud=BAUD_RATE)

    apps = [
        ClockApp("Relógio", fonts),
        WeatherApp("Clima", fonts),
        MTSApp("Metros", fonts),
        FootballApp("Futebol", fonts),
        MarketApp("Mercados", fonts)
    ]
    
    current_idx = 0
    # Carregamento inicial
    apps[current_idx].update_data()

    last_update_check = time.time()

    try:
        while True:
            # Verifica atualizações do Git periodicamente
            if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
                update_from_git()
                last_update_check = time.time()

            current_app = apps[current_idx]
            next_idx = (current_idx + 1) % len(apps)
            next_app = apps[next_idx]

            start_time = time.time()
            fetch_started = False

            while True:
                # 1. Desenha a app atual
                frame = current_app.draw()
                renderer.display(frame)
                time.sleep(0.1)

                elapsed = time.time() - start_time
                
                # 2. Quando o tempo acaba, inicia fetch da próxima
                if elapsed >= current_app.duration and not fetch_started:
                    threading.Thread(target=fetch_data_async, args=(next_app,), daemon=True).start()
                    fetch_started = True

                # 3. Troca assim que o fetch terminar
                if fetch_started and not next_app.is_updating:
                    if next_app.duration > 0:
                        current_idx = next_idx
                        apps[current_idx].reset_app() # Inicia o timer da nova app
                        break
                    else:
                        # Se a próxima for vazia, passa para a seguinte
                        next_idx = (next_idx + 1) % len(apps)
                        next_app = apps[next_idx]
                        fetch_started = False 

    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        renderer.close()

if __name__ == "__main__":
    main()
