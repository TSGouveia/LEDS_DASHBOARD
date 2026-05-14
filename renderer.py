import serial
import numpy as np
import cv2

class LEDRenderer:
    def __init__(self, port_finder_func, width=32, height=18, baud=1000000):
        self.width = width
        self.height = height
        self.baud = baud
        self.port_finder = port_finder_func
        self.start_bytes = bytes([0xA5, 0x5A])
        self.ser = None
        self.port = None
        self._connect()

    def _connect(self):
        """Tenta estabelecer a conexão serial."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        self.port = self.port_finder()
        if not self.port:
            print("[RENDERER] Nenhuma porta serial encontrada. Aguardando...")
            return False

        try:
            # timeout=1 para leitura, write_timeout=0.2 para escrita (baseado no script que funciona)
            self.ser = serial.Serial(self.port, self.baud, timeout=1.0, write_timeout=0.2)
            self.ser.reset_output_buffer()
            print(f"[RENDERER] Conectado à porta {self.port}")
            return True
        except Exception as e:
            print(f"[RENDERER] Erro ao conectar na porta {self.port}: {e}")
            return False

    def _prepare_linear(self, frame_rgb):
        """Prepara os dados em formato RGB linear com rotação de 180 graus."""
        # 1. Rotação de 180 graus (conforme o hardware exige agora)
        frame_rgb = cv2.rotate(frame_rgb, cv2.ROTATE_180)

        # 2. Garante que a matriz tem o tamanho esperado
        if frame_rgb.shape[:2] != (self.height, self.width):
            frame_rgb = cv2.resize(frame_rgb, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

        # 3. Retorna os bytes em formato linear: R, G, B, R, G, B...
        # .flatten() garante a sequência correta e .tobytes() converte para bytes
        return frame_rgb.flatten().tobytes()

    def display(self, frame_rgb):
        """Envia o frame para os LEDs com tentativa de reconexão."""
        if not self.ser or not self.ser.is_open:
            if not self._connect():
                return

        try:
            payload = self._prepare_linear(frame_rgb)
            expected_len = self.width * self.height * 3
            if len(payload) == expected_len:
                # Envia o pacote: [0xA5, 0x5A, R, G, B, ...]
                self.ser.write(self.start_bytes + payload)
            else:
                print(f"[RENDERER] Erro: Payload com {len(payload)} bytes, esperado {expected_len}")
        except Exception as e:
            print(f"[RENDERER] Erro ao enviar para serial: {e}. Tentando reconectar...")
            self.ser = None # Força reconexão na próxima chamada

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
