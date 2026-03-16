#pragma once
#include "Renderer.h"
#include "Fonts.h"
#include <FastLED.h>
#include <LEDMatrix.h>

class FontLoader {
public:
    void drawChar3x5(Renderer& renderer, cLEDMatrixBase& leds, char c, int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void drawChar5x9(Renderer& renderer, cLEDMatrixBase& leds, char c, int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void drawText3x5(Renderer& renderer, cLEDMatrixBase& leds, const char* text, int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void drawText5x9(Renderer& renderer, cLEDMatrixBase& leds, const char* text, int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void drawWeatherIcon(Renderer& renderer, cLEDMatrixBase& leds, const char* name, int x, int y, int area_w = -1, int area_h = -1);
};
