#include "FontLoader.h"
#include <ctype.h>
#include <string.h>

void FontLoader::drawChar3x5(Renderer& renderer, cLEDMatrixBase& leds, char c, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    c = toupper(c);
    for (size_t i = 0; i < map_3x5_size; i++) {
        if (map_3x5[i].name == c) {
            const uint8_t* data = map_3x5[i].data;
            uint8_t w = map_3x5[i].width;
            uint8_t h = map_3x5[i].height;
            for (uint8_t dy = 0; dy < h; dy++) {
                for (uint8_t dx = 0; dx < w; dx++) {
                    if (data[dy * w + dx] > 0) renderer.setPixel(leds, x + dx, y + dy, r, g, b);
                }
            }
            break;
        }
    }
}

void FontLoader::drawChar5x9(Renderer& renderer, cLEDMatrixBase& leds, char c, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    c = toupper(c);
    for (size_t i = 0; i < map_5x9_size; i++) {
        if (map_5x9[i].name == c) {
            const uint8_t* data = map_5x9[i].data;
            uint8_t w = map_5x9[i].width;
            uint8_t h = map_5x9[i].height;
            for (uint8_t dy = 0; dy < h; dy++) {
                for (uint8_t dx = 0; dx < w; dx++) {
                    if (data[dy * w + dx] > 0) renderer.setPixel(leds, x + dx, y + dy, r, g, b);
                }
            }
            break;
        }
    }
}

void FontLoader::drawText3x5(Renderer& renderer, cLEDMatrixBase& leds, const char* text, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    int curr_x = x;
    while (*text) {
        if (*text == ' ') curr_x += 2;
        else { drawChar3x5(renderer, leds, *text, curr_x, y, r, g, b); curr_x += 4; }
        text++;
    }
}

void FontLoader::drawText5x9(Renderer& renderer, cLEDMatrixBase& leds, const char* text, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    int curr_x = x;
    while (*text) {
        if (*text == ' ') curr_x += 2;
        else { drawChar5x9(renderer, leds, *text, curr_x, y, r, g, b); curr_x += 6; }
        text++;
    }
}

void FontLoader::drawWeatherIcon(Renderer& renderer, cLEDMatrixBase& leds, const char* name, int x, int y, int area_w, int area_h) {
    for (size_t i = 0; i < map_weather_size; i++) {
        if (strcmp(map_weather[i].name, name) == 0) {
            const uint8_t* data = map_weather[i].data;
            uint8_t w = map_weather[i].width;
            uint8_t h = map_weather[i].height;
            
            int start_x = (x == -1 && area_w > 0) ? (area_w - w) / 2 : x;
            int start_y = (y == -1 && area_h > 0) ? (area_h - h) / 2 : y;
            
            for (uint8_t dy = 0; dy < h; dy++) {
                for (uint8_t dx = 0; dx < w; dx++) {
                    int base = (dy * w + dx) * 4;
                    uint8_t r = data[base + 0];
                    uint8_t g = data[base + 1];
                    uint8_t b = data[base + 2];
                    uint8_t a = data[base + 3];
                    if (a > 128) renderer.setPixel(leds, start_x + dx, start_y + dy, r, g, b);
                }
            }
            break;
        }
    }
}
