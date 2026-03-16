#pragma once
#include <Arduino.h>
#include <FastLED.h>
#include <LEDMatrix.h>

class Renderer {
private:
    uint8_t width;
    uint8_t height;

public:
    Renderer(uint8_t w = 32, uint8_t h = 18);
    void clear(cLEDMatrixBase& leds);
    void setPixel(cLEDMatrixBase& leds, int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void fillRect(cLEDMatrixBase& leds, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b);
};
