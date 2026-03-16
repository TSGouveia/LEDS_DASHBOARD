#include "Renderer.h"

Renderer::Renderer(uint8_t w, uint8_t h) : width(w), height(h) {}

void Renderer::clear(cLEDMatrixBase& leds) {
    FastLED.clear();
}

void Renderer::setPixel(cLEDMatrixBase& leds, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    if (x >= 0 && x < width && y >= 0 && y < height) {
        // Usamos o Y lógico diretamente (0 no topo)
        int physical_y = y;
        
        // Zigzag: inverte X em linhas ímpares (1, 3, 5...)
        int tx = (y % 2 != 0) ? (width - 1 - x) : x;
        
        leds(tx, physical_y) = CRGB(r, g, b);
    }
}

void Renderer::fillRect(cLEDMatrixBase& leds, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b) {
    for (int i = 0; i < w; i++) {
        for (int j = 0; j < h; j++) {
            setPixel(leds, x + i, y + j, r, g, b);
        }
    }
}
