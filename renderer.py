import serial
import numpy as np

class LEDRenderer:
    def __init__(self, port, width=32, height=18, baud=1000000):
        self.width = width
        self.height = height
        self.start_bytes = bytes([0xA5, 0x5A])
        # Aumentar o timeout para garantir que o buffer é enviado
        self.ser = serial.Serial(port, baud, timeout=1.0)
        self.ser.reset_output_buffer()

    def _to_zigzag(self, frame_rgb):
        """Converte a matriz RGB para o formato de fiação da mesa."""
        # Garante que a matriz tem o tamanho esperado
        if frame_rgb.shape[:2] != (self.height, self.width):
            # Redimensiona se necessário (segurança)
            import cv2
            frame_rgb = cv2.resize(frame_rgb, (self.width, self.height), interpolation=cv2.INTER_NEAREST)

        frame = np.ascontiguousarray(frame_rgb, dtype=np.uint8)
        zigzag_frame = frame.copy()
        zigzag_frame[1::2, :] = zigzag_frame[1::2, ::-1]
        return zigzag_frame.tobytes()

    def display(self, frame_rgb):
        """Envia o frame para os LEDs."""
        try:
            payload = self._to_zigzag(frame_rgb)
            # 32 * 18 * 3 = 1728 bytes
            expected_len = self.width * self.height * 3
            if len(payload) == expected_len:
                self.ser.write(self.start_bytes + payload)
            else:
                print(f"Erro: Payload com {len(payload)} bytes, esperado {expected_len}")
        except Exception as e:
            print(f"Erro ao enviar para serial: {e}")

    def close(self):
        if self.ser.is_open:
            self.ser.close()
