import os
import cv2
import numpy as np

class FontLoader:
    def __init__(self, base_path="fonts"):
        self.fonts = {"3x5": {}, "5x9": {}, "weather": {}}
        for size in self.fonts.keys():
            folder = os.path.join(base_path, size)
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.endswith(".bmp"):
                        name = file.split(".")[0].upper()
                        if size == "weather":
                            img = cv2.imread(os.path.join(folder, file), cv2.IMREAD_UNCHANGED)
                            if img is not None:
                                if img.shape[2] == 4:
                                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
                                else:
                                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                self.fonts[size][name] = img
                        else:
                            img = cv2.imread(os.path.join(folder, file), cv2.IMREAD_GRAYSCALE)
                            if img is not None:
                                _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
                                self.fonts[size][name] = binary

    def draw_char(self, canvas, char, x, y, size, color):
        char_key = str(char).upper()
        if char_key in self.fonts[size]:
            bitmap = self.fonts[size][char_key]
            h_bmp, w_bmp = bitmap.shape[:2]
            for dy in range(h_bmp):
                for dx in range(w_bmp):
                    ty, tx = y + dy, x + dx
                    if 0 <= ty < canvas.shape[0] and 0 <= tx < canvas.shape[1]:
                        if bitmap[dy, dx] > 0:
                            canvas[ty, tx] = color

    def draw_bitmap(self, canvas, name, x, y, size="weather", area_w=None, area_h=None):
        """
        Desenha um bitmap. 
        Se x=-1 e area_w for definida, centra em X nessa área.
        Se y=-1 e area_h for definida, centra em Y nessa área.
        """
        if name in self.fonts[size]:
            bitmap = self.fonts[size][name]
            h_bmp, w_bmp = bitmap.shape[:2]
            
            start_x = (area_w - w_bmp) // 2 if x == -1 and area_w else x
            start_y = (area_h - h_bmp) // 2 if y == -1 and area_h else y

            for dy in range(h_bmp):
                ty = start_y + dy
                if 0 <= ty < canvas.shape[0]:
                    for dx in range(w_bmp):
                        tx = start_x + dx
                        if 0 <= tx < canvas.shape[1]:
                            pixel = bitmap[dy, dx]
                            # Se tiver canal Alfa, usa-o. Se não, usa qualquer cor > 0
                            if len(pixel) == 4:
                                if pixel[3] > 128: canvas[ty, tx] = pixel[:3]
                            else:
                                if any(pixel > 0): canvas[ty, tx] = pixel[:3]

    def draw_text(self, canvas, text, x, y, size, color):
        curr_x = x
        for char in str(text).upper():
            if char == " ":
                curr_x += 2
                continue
            char_key = "COLON" if char == ":" else char
            if char_key in self.fonts[size]:
                bitmap = self.fonts[size][char_key]
                w = bitmap.shape[1]
                self.draw_char(canvas, char_key, curr_x, y, size, color)
                curr_x += w + 1
