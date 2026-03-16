import numpy as np

class BaseApp:
    def __init__(self, name, font_loader):
        self.name = name
        self.font_loader = font_loader
        self.width = 32
        self.height = 18
        self.data = {}
        self.duration = 10
        self.is_updating = False # Flag para saber se a API está a correr

    def update_data(self):
        """Lógica de API"""
        pass

    def reset_app(self):
        """Chamado quando a app começa a ser exibida"""
        pass

    def draw(self):
        """Retorna o canvas RGB 32x18"""
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
