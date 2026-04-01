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

# --- CONFIGURAÇÃO ---
BAUD_RATE = 1000000
UPDATE_CHECK_INTERVAL = 30    # Verificação do Git a cada 30 segundos
INITIAL_CLOCK_DURATION = 300  # 5 minutos de relógio no arranque

def fetch_data_async(app):
    app.is_updating = True
    app.update_data()
    app.is_updating = False

def show_update_screen(renderer, fonts):
    """Desenha um ecrã de 'UPDATING' nos LEDs antes de reiniciar."""
    canvas = np.zeros((18, 32, 3), dtype=np.uint8)
    color = (0, 255, 255) # Ciano para ser bem legível na fonte 3x5
    
    # "UPDATING" tem 8 letras. Na fonte 3x5 (3 largura + 1 espaço = 4px por letra)
    # 8 * 4 = 32 pixels. Cabe exatamente de uma ponta à outra.
    text = "UPDATING"
    for i, char in enumerate(text):
        fonts.draw_char(canvas, char, i * 4, 7, "3x5", color)
    
    renderer.display(canvas)
    time.sleep(2) # Dar tempo para o utilizador ver a mensagem

def main():
    fonts = FontLoader()
    renderer = LEDRenderer(find_serial_port, width=32, height=18, baud=BAUD_RATE)

    # Inicializamos as apps
    clock_app = ClockApp("Relógio", fonts)
    apps = [
        clock_app,
        WeatherApp("Clima", fonts),
        MTSApp("Metros", fonts),
        FootballApp("Futebol", fonts),
        MarketApp("Mercados", fonts)
    ]
    
    # 1. Fase Inicial: Mostrar apenas o Relógio durante 5 minutos
    print(f"[MAIN] Fase inicial: Mostrando {clock_app.name} por {INITIAL_CLOCK_DURATION}s")
    clock_app.update_data()
    start_up_time = time.time()
    last_update_check = time.time()
    
    try:
        while time.time() - start_up_time < INITIAL_CLOCK_DURATION:
            frame = clock_app.draw()
            renderer.display(frame)
            time.sleep(0.1)
            
            # Mesmo no arranque, verifica updates a cada 30s
            if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
                if update_from_git():
                    show_update_screen(renderer, fonts)
                    print("[MAIN] Update detectado no arranque. Reiniciando...")
                    return
                last_update_check = time.time()

        print("[MAIN] Fim da fase inicial. Iniciando ciclo de apps.")

        # 2. Ciclo Normal de Apps
        current_idx = 0
        apps[current_idx].update_data()

        while True:
            # Verifica atualizações do Git periodicamente (30s)
            if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
                if update_from_git():
                    show_update_screen(renderer, fonts)
                    print("[MAIN] Reiniciando serviço para aplicar atualizações...")
                    return 
                last_update_check = time.time()

            current_app = apps[current_idx]
            next_idx = (current_idx + 1) % len(apps)
            next_app = apps[next_idx]

            start_time = time.time()
            fetch_started = False

            while True:
                frame = current_app.draw()
                renderer.display(frame)
                time.sleep(0.1)

                elapsed = time.time() - start_time
                
                if elapsed >= current_app.duration and not fetch_started:
                    threading.Thread(target=fetch_data_async, args=(next_app,), daemon=True).start()
                    fetch_started = True

                # Verificação de update mesmo durante o ciclo de uma app
                if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
                    if update_from_git():
                        show_update_screen(renderer, fonts)
                        return
                    last_update_check = time.time()

                if fetch_started and not next_app.is_updating:
                    if next_app.duration > 0:
                        current_idx = next_idx
                        apps[current_idx].reset_app()
                        break
                    else:
                        next_idx = (next_idx + 1) % len(apps)
                        next_app = apps[next_idx]
                        fetch_started = False 

    except KeyboardInterrupt:
        print("\nDesligando sistema...")
    finally:
        renderer.close()

if __name__ == "__main__":
    main()
