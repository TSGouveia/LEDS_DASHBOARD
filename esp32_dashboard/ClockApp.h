#pragma once
#include "App.h"
#include <NTPClient.h>
#include <time.h>

extern NTPClient timeClient;

class ClockApp : public App {
public:
    void updateData() override {}

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        renderer.clear(leds);
        
        // Obter o tempo de forma segura
        time_t rawTime = (time_t)timeClient.getEpochTime();
        struct tm *ptm = gmtime(&rawTime);

        // Se o ano for menor que 1970, o NTP ainda não sincronizou bem
        if (ptm->tm_year < 70) {
            // Desenha apenas um erro se não sincronizar
            fontLoader.drawText3x5(renderer, leds, "SYNCING", 2, 7, 255, 0, 0);
            return;
        }

        int h = timeClient.getHours();
        int m = timeClient.getMinutes();
        int s = timeClient.getSeconds();
        int d = ptm->tm_mday;
        int mo = ptm->tm_mon + 1;

        char h_str[3], m_str[3], d_str[3], mo_str[3];
        sprintf(h_str, "%02d", h);
        sprintf(m_str, "%02d", m);
        sprintf(d_str, "%02d", d);
        sprintf(mo_str, "%02d", mo);

        uint8_t r = 255, g = 255, b = 255;

        // 1. HORAS (Font 5x9)
        fontLoader.drawChar5x9(renderer, leds, h_str[0], 1, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, h_str[1], 7, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, m_str[0], 20, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, m_str[1], 26, 1, r, g, b);

        // 2. PONTOS RELÓGIO (Blink 1Hz)
        if (s % 2 == 0) {
            renderer.fillRect(leds, 15, 2, 2, 2, r, g, b);
            renderer.fillRect(leds, 15, 7, 2, 2, r, g, b);
        }

        // 3. DATA (Font 3x5)
        fontLoader.drawChar3x5(renderer, leds, d_str[0], 7, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, d_str[1], 11, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, mo_str[0], 18, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, mo_str[1], 22, 12, r, g, b);

        // 4. TRAÇO DATA
        renderer.fillRect(leds, 15, 14, 2, 1, r, g, b);
    }

    int getDuration() override {
        return 10;
    }
};
