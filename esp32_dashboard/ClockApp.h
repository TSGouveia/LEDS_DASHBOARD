#pragma once
#include "App.h"
#include <RTC.h> // Importante para ler o hardware diretamente
#include <time.h>

class ClockApp : public App {
public:
    void updateData() override {}

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        renderer.clear(leds);
        
        // 1. Obter o tempo diretamente do hardware RTC do R4
        RTCTime currentTime;
        RTC.getTime(currentTime);
        
        // 2. Converter para o formato padrão Unix para aplicar o fuso horário
        time_t unixNow = currentTime.getUnixTime();
        struct tm timeinfo;
        
        // 3. Aplicar a regra de Lisboa (TZ_INFO do setup)
        localtime_r(&unixNow, &timeinfo);

        // DEBUG no Serial Monitor
        //Serial.print("Ano: "); Serial.print(timeinfo.tm_year + 1900);
        //Serial.print(" Hora: "); Serial.println(timeinfo.tm_hour);

        // Se o ano for menor que 2024, ainda não sincronizou
        if (timeinfo.tm_year + 1900 < 2024) { 
            fontLoader.drawText3x5(renderer, leds, "SYNCING", 2, 7, 255, 0, 0);
            return;
        }

        // --- Variáveis para o Desenho ---
        int h  = timeinfo.tm_hour;
        int m  = timeinfo.tm_min;
        int s  = timeinfo.tm_sec;
        int d  = timeinfo.tm_mday;
        int mo = timeinfo.tm_mon + 1;

        char h_str[3], m_str[3], d_str[3], mo_str[3];
        sprintf(h_str, "%02d", h);
        sprintf(m_str, "%02d", m);
        sprintf(d_str, "%02d", d);
        sprintf(mo_str, "%02d", mo);

        uint8_t r = 255, g = 255, b = 255;

        // Desenho das Horas e Minutos
        fontLoader.drawChar5x9(renderer, leds, h_str[0], 1, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, h_str[1], 7, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, m_str[0], 20, 1, r, g, b);
        fontLoader.drawChar5x9(renderer, leds, m_str[1], 26, 1, r, g, b);

        // Pontos a piscar
        if (s % 2 == 0) {
            renderer.fillRect(leds, 15, 2, 2, 2, r, g, b);
            renderer.fillRect(leds, 15, 7, 2, 2, r, g, b);
        }

        // Data
        fontLoader.drawChar3x5(renderer, leds, d_str[0], 7, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, d_str[1], 11, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, mo_str[0], 18, 12, r, g, b);
        fontLoader.drawChar3x5(renderer, leds, mo_str[1], 22, 12, r, g, b);
        renderer.fillRect(leds, 15, 14, 2, 1, r, g, b);
    }

    int getDuration() override { return 10; }
};