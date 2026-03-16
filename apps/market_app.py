import yfinance as yf
from .base_app import BaseApp
import numpy as np
import time

class MarketApp(BaseApp):
    def __init__(self, name, font_loader):
        super().__init__(name, font_loader)
        self.tickers = {
            "BTC": "BTC-EUR",
            "S&P": "^GSPC"
        }
        self.data = {
            "BTC": {"points": np.zeros(32), "now": 0, "change": 0, "has": False},
            "S&P": {"points": np.zeros(32), "now": 0, "change": 0, "has": False}
        }
        self.last_update = 0
        self.display_start_time = time.time()
        self.duration = 40  # 20s cada

    def get_text_width(self, text):
        return (len(str(text)) * 3) + (len(str(text)) - 1)

    def update_data(self):
        now = time.time()
        if now - self.last_update < 300 and all(v["has"] for v in self.data.values()):
            return

        for label, symbol in self.tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                # "7d" traz o histórico da última semana (168h para BTC, 5 dias úteis para S&P)
                hist_data = ticker.history(period="7d", interval="1h")['Close'].dropna()
                
                if len(hist_data) > 0:
                    full_pts = hist_data.values
                    start_price = full_pts[0]
                    end_price = full_pts[-1]
                    
                    # Interpolação para 32 pixéis
                    indices_orig = np.arange(len(full_pts))
                    indices_new = np.linspace(0, len(full_pts) - 1, 32)
                    pts = np.interp(indices_new, indices_orig, full_pts)
                    
                    self.data[label]["points"] = pts
                    self.data[label]["now"] = end_price
                    self.data[label]["change"] = ((end_price - start_price) / start_price) * 100
                    self.data[label]["has"] = True
                    
                    # DEBUG DETALHADO PARA VERIFICAÇÃO
                    print(f"\n[MARKET VERIFY - {label}]")
                    print(f"- Início (há 7 dias): {start_price:.2f}")
                    print(f"- Agora: {end_price:.2f}")
                    print(f"- Variação: {self.data[label]['change']:+.2f}%")
                    print(f"- Pontos extraídos: {len(full_pts)}")
                    print(f"--------------------------")
            except Exception as e:
                print(f"Erro Market {label}: {e}")

        self.last_update = now

    def draw_graph(self, canvas, label):
        d = self.data[label]
        pts = d["points"]
        now_val = d["now"]
        
        is_up = d["change"] >= 0
        color = (0, 255, 0) if is_up else (255, 0, 0)
        dim_color = (0, 30, 0) if is_up else (30, 0, 0)
        white = (255, 255, 255)

        # Normalização sem padding: usa a altura máxima disponível abaixo do texto (12px)
        min_p, max_p = np.min(pts), np.max(pts)
        p_range = max_p - min_p if max_p > min_p else 1

        for x in range(32):
            norm = (pts[x] - min_p) / p_range
            # y vai de 17 (fundo) até 6 (logo abaixo do texto que termina em y=5)
            y = 17 - int(norm * 11)
            
            canvas[y, x] = color
            if y < 17:
                canvas[y+1:18, x] = dim_color

        # Texto no Topo (y=1)
        self.font_loader.draw_text(canvas, label, 1, 1, "3x5", white)
        
        if label == "BTC":
            # Arredondamento para 1 casa decimal (ex: 94.6K)
            val_k = round(now_val / 1000.0, 1)
            integers = int(val_k)
            decimals = int(round((val_k - integers) * 10))
            if decimals >= 10: # Caso o round salte para 10
                integers += 1
                decimals = 0
                
            int_str = str(integers)
            dec_str = f"{decimals}K"
            
            w_int = self.get_text_width(int_str)
            w_dec = self.get_text_width(dec_str)
            total_w = w_int + 3 + w_dec
            
            sx = 31 - total_w
            self.font_loader.draw_text(canvas, int_str, sx, 1, "3x5", white)
            dot_x = sx + w_int + 1
            if 0 <= dot_x < 32:
                canvas[5, dot_x] = white # Ponto na base
            self.font_loader.draw_text(canvas, dec_str, dot_x + 2, 1, "3x5", white)
        else:
            # S&P Arredondado para inteiro
            price_str = f"{int(round(now_val))}"
            tw = self.get_text_width(price_str)
            self.font_loader.draw_text(canvas, price_str, 31 - tw, 1, "3x5", white)

    def draw(self):
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        elapsed = time.time() - self.display_start_time
        
        # Alterna entre BTC e S&P a cada 20 segundos
        show_label = "BTC" if elapsed < 20 else "S&P"
        
        if self.data[show_label]["has"]:
            self.draw_graph(canvas, show_label)
        else:
            # Fallback se um falhar
            other = "S&P" if show_label == "BTC" else "BTC"
            if self.data[other]["has"]:
                self.draw_graph(canvas, other)
                
        return canvas

    def reset_app(self):
        self.display_start_time = time.time()
