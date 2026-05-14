import numpy as np
import time
from .base_app import BaseApp

class TestApp(BaseApp):
    def __init__(self, name, font_loader, duration=10):
        super().__init__(name, font_loader)
        self.duration = duration
        self.start_time = 0

    def reset_app(self):
        self.start_time = time.time()

    def draw(self):
        # Canvas de 18x32
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        elapsed = time.time() - self.start_time
        
        # Divide o tempo total em 4 partes
        quarter = self.duration / 4
        
        if elapsed < quarter:
            color = (255, 255, 255) # Branco
        elif elapsed < 2 * quarter:
            color = (255, 0, 0)     # Vermelho
        elif elapsed < 3 * quarter:
            color = (0, 255, 0)     # Verde
        else:
            color = (0, 0, 255)     # Azul
            
        canvas[:] = color
        return canvas
