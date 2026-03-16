from .base_app import BaseApp
from datetime import datetime
import numpy as np


class ClockApp(BaseApp):
    def draw(self):
        # Fundo preto (32x18 garantido pela base_app)
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        now = datetime.now()
        white = (255, 255, 255)

        # 1. HORAS (Font 5x9) - Topo em y=1
        h_str = now.strftime("%H")
        m_str = now.strftime("%M")

        self.font_loader.draw_char(canvas, h_str[0], 1, 1, "5x9", white)
        self.font_loader.draw_char(canvas, h_str[1], 7, 1, "5x9", white)
        self.font_loader.draw_char(canvas, m_str[0], 20, 1, "5x9", white)
        self.font_loader.draw_char(canvas, m_str[1], 26, 1, "5x9", white)

        # 2. PONTOS RELÓGIO (Blink 1Hz)
        if now.second % 2 == 0:
            # Ponto Superior (x:15,16 | y:2,3)
            canvas[2:4, 15:17] = white
            # Ponto Inferior (x:15,16 | y:7,8)
            canvas[7:9, 15:17] = white

        # 3. DATA (Font 3x5) - Topo em y=12 para ficar bem posicionada
        d_str = now.strftime("%d")
        mo_str = now.strftime("%m")

        # Dia: 7,12 e 11,12 | Mês: 18,12 e 22,12
        self.font_loader.draw_char(canvas, d_str[0], 7, 12, "3x5", white)
        self.font_loader.draw_char(canvas, d_str[1], 11, 12, "3x5", white)
        self.font_loader.draw_char(canvas, mo_str[0], 18, 12, "3x5", white)
        self.font_loader.draw_char(canvas, mo_str[1], 22, 12, "3x5", white)

        # 4. TRAÇO DATA (x:15,16 | y:14)
        canvas[14, 15:17] = white

        return canvas
