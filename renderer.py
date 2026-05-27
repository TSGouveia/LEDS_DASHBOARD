import serial
import numpy as np
import cv2
import threading
import time

class LEDRenderer:
    def __init__(self, port_finder_func, width=32, height=18, baud=1000000):
        self.width = width
        self.height = height
        self.baud = baud
        self.port_finder = port_finder_func
        self.start_bytes = bytes([0xA5, 0x5A])
        self.ser = None
        self.port = None
        
        # Gestão de Frames e Thread
        self.current_frame = np.zeros((height, width, 3), dtype=np.uint8)
        self.lock = threading.Lock()
        self.running = True
        
        self._connect()
        
        # Inicia a thread de envio contínuo (20Hz para suavidade)
        self.thread = threading.Thread(target=self._render_worker, daemon=True)
        self.thread.start()

    def _connect(self):
        """Tenta estabelecer a conexão serial."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        self.port = self.port_finder()
        if not self.port:
            print("[RENDERER] Nenhuma porta serial encontrada. Aguardando...")
            return False

        try:
            # timeout=1 para leitura, write_timeout=0.2 para escrita
            self.ser = serial.Serial(self.port, self.baud, timeout=1.0, write_timeout=0.2)
            self.ser.reset_output_buffer()
            print(f"[RENDERER] Conectado à porta {self.port}")
            return True
        except Exception as e:
            print(f"[RENDERER] Erro ao conectar na porta {self.port}: {e}")
            return False

    def _prepare_linear(self, frame_rgb):
        """Prepara os dados em formato RGB linear com rotação de 180 graus."""
        # 1. Rotação de 180 graus
        frame_rgb = np.rot90(frame_rgb, k=2)

        # 2. Garante que a matriz tem o tamanho esperado
        if frame_rgb.shape[:2] != (self.height, self.width):
            frame_rgb = cv2.resize(frame_rgb, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

        # 3. Retorna os bytes em formato linear: R, G, B, R, G, B...
        return frame_rgb.flatten().tobytes()

    def _render_worker(self):
        """Thread que envia continuamente o frame atual para os LEDs."""
        frame_delay = 1.0 / 20 # 20Hz
        while self.running:
            start_time = time.monotonic()
            
            with self.lock:
                frame = self.current_frame.copy()
            
            self._send_to_serial(frame)
            
            elapsed = time.monotonic() - start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _send_to_serial(self, frame_rgb):
        """Lógica interna de envio para a porta serial."""
        if not self.ser or not self.ser.is_open:
            if not self._connect():
                return

        try:
            payload = self._prepare_linear(frame_rgb)
            expected_len = self.width * self.height * 3
            if len(payload) == expected_len:
                self.ser.write(self.start_bytes + payload)
            else:
                print(f"[RENDERER] Erro: Payload com {len(payload)} bytes, esperado {expected_len}")
        except Exception as e:
            print(f"[RENDERER] Erro ao enviar para serial: {e}. Tentando reconectar...")
            self.ser = None

    def display(self, frame_rgb):
        """Apenas atualiza o frame que a thread de worker vai enviar."""
        with self.lock:
            self.current_frame = frame_rgb

    def close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
