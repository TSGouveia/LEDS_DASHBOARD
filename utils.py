import serial.tools.list_ports
import subprocess
import time

def find_serial_port():
    """Tenta encontrar automaticamente a porta serial do ESP32 ou Arduino."""
    ports = serial.tools.list_ports.comports()
    # IDs comuns para ESP32 e Arduino
    common_hwids = [
        "10C4:EA60", # CP210x
        "1A86:7523", # CH340
        "1A86:55D4", # CH9102
        "2341:006D", # Arduino UNO WiFi R4
        "2341:0043", # Arduino Uno R3
    ]
    
    for port in ports:
        # No Linux, port.device será algo como /dev/ttyACM0 ou /dev/ttyUSB0
        print(f"Detectada porta: {port.device} - {port.description} [{port.hwid}]")
        for hwid in common_hwids:
            if hwid.lower() in port.hwid.lower():
                return port.device
                
    # Se não encontrar por HWID, tenta pela descrição ou nome do dispositivo (Linux/macOS/Windows)
    for port in ports:
        dev = port.device.upper()
        desc = port.description.upper()
        if any(x in dev for x in ["TTYACM", "TTYUSB", "COM"]) or "SERIAL" in desc or "ARDUINO" in desc:
            return port.device
            
    return None

def update_from_git():
    """Verifica e puxa atualizações do git."""
    try:
        # Garante que estamos na branch correta e fetch
        subprocess.run(["git", "fetch"], check=True, capture_output=True)
        
        # Compara com o remote
        status = subprocess.run(
            ["git", "status", "-uno"], 
            check=True, 
            capture_output=True, 
            text=True
        ).stdout
        
        if "Your branch is behind" in status or "pode ser atualizado" in status:
            print("\n[UPDATE] Nova versão detectada! Atualizando...")
            subprocess.run(["git", "pull"], check=True)
            print("[UPDATE] Atualização concluída. O sistema pode precisar de reiniciar.\n")
            return True
    except Exception as e:
        print(f"[UPDATE] Erro ao verificar atualizações: {e}")
    return False
