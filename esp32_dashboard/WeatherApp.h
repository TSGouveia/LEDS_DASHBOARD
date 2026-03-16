#pragma once
#include "App.h"
#include <WiFiS3.h>

class WeatherApp : public App {
private:
    struct WeatherData { int temp = 0; int precip = 0; String icon = "SUN"; };
    WeatherData today, tomorrow;
    unsigned long lastUpdate = 0;
    unsigned long displayStartTime = 0;
    bool hasData = false;

    String getIconName(int id) {
        if (id == 1) return "SUN";
        if (id == 2 || id == 3) return "CLOUDSUN";
        if (id == 4 || id == 5 || (id >= 16 && id <= 17) || (id >= 24 && id <= 27)) return "CLOUD";
        if (id == 6 || id == 7 || id == 9 || id == 10 || id == 12 || id == 13 || id == 15 || id == 18 || (id >= 28 && id <= 30)) return "RAIN";
        return "HEAVYRAIN";
    }

    int getTextWidth(const char* text) {
        int len = strlen(text);
        return (len > 0) ? (len * 3) + (len - 1) : 0;
    }

    float findValue(WiFiClient& client, const char* key) {
        if (client.find(key)) {
            client.find(":");
            String val = "";
            while (client.peek() == ' ' || client.peek() == '"' || client.peek() == ':') client.read();
            while ((client.peek() >= '0' && client.peek() <= '9') || client.peek() == '.' || client.peek() == '-') {
                val += (char)client.read();
            }
            return (val.length() > 0) ? val.toFloat() : -99.0;
        }
        return -99.0;
    }

    String findString(WiFiClient& client, const char* key) {
        if (client.find(key)) {
            client.find(":");
            while (client.peek() == ' ' || client.peek() == '"') client.read();
            return client.readStringUntil('"');
        }
        return "";
    }

public:
    void resetApp() override { displayStartTime = millis(); }

    void updateData() override {
        if (millis() - lastUpdate < 600000 && hasData) return; 
        WiFiClient client;
        
        // 1. Buscar Precipitação da API Daily (Índice 0 e 1)
        if (client.connect("api.ipma.pt", 80)) {
            client.println("GET /open-data/forecast/meteorology/cities/daily/1110600.json HTTP/1.1");
            client.println("Host: api.ipma.pt");
            client.println("Connection: close"); client.println();
            while (client.connected() && !client.available()) delay(1);
            while (client.connected()) { if (client.readStringUntil('\n') == "\r") break; }
            
            int count = 0;
            while ((client.connected() || client.available()) && count < 2) {
                float p = findValue(client, "\"precipitaProb\"");
                if (p != -99.0) {
                    if (count == 0) today.precip = (int)p;
                    else tomorrow.precip = (int)p;
                    count++;
                }
            }
            client.stop();
        }

        // 2. Buscar Temperatura e ID da API Aggregate
        if (client.connect("api.ipma.pt", 80)) {
            client.println("GET /public-data/forecast/aggregate/1150322.json HTTP/1.1");
            client.println("Host: api.ipma.pt");
            client.println("Connection: close"); client.println();
            while (client.connected() && !client.available()) delay(1);
            while (client.connected()) { if (client.readStringUntil('\n') == "\r") break; }
            
            String dateToday = "";
            bool foundToday = false, foundTomorrow = false;
            while (client.connected() || client.available()) {
                String dPrev = findString(client, "\"dataPrev\"");
                if (dPrev == "") continue;
                if (dateToday == "") dateToday = dPrev.substring(0, 10);
                
                // Pega a primeira entrada de hoje (mais próxima do início do dia/agora)
                if (!foundToday && dPrev.startsWith(dateToday)) {
                    float t = findValue(client, "\"tMed\"");
                    if (t == -99.0) t = findValue(client, "\"tMax\"");
                    float id = findValue(client, "\"idTipoTempo\"");
                    today.temp = (int)t;
                    today.icon = getIconName((int)id);
                    foundToday = true;
                } 
                // Pega a entrada das 12:00 de amanhã
                else if (!foundTomorrow && dPrev.substring(0, 10) != dateToday && dPrev.endsWith("T12:00:00")) {
                    float t = findValue(client, "\"tMed\"");
                    if (t == -99.0) t = findValue(client, "\"tMax\"");
                    float id = findValue(client, "\"idTipoTempo\"");
                    tomorrow.temp = (int)t;
                    tomorrow.icon = getIconName((int)id);
                    foundTomorrow = true;
                    break; 
                }
            }
            if (foundToday) { hasData = true; lastUpdate = millis(); }
            client.stop();
        }
    }

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        if (!hasData) return;
        unsigned long elapsed = millis() - displayStartTime;
        bool showT = (elapsed > 30000); // 30s hoje, 30s amanha
        WeatherData& d = showT ? tomorrow : today;
        renderer.clear(leds);
        fontLoader.drawWeatherIcon(renderer, leds, d.icon.c_str(), 0, 3);
        char tB[8], pB[8];
        sprintf(tB, "%dC", d.temp);
        fontLoader.drawText3x5(renderer, leds, tB, 31 - getTextWidth(tB), 1, 255, 255, 255);
        sprintf(pB, "%d", d.precip);
        int px = 31 - (getTextWidth(pB) + 4);
        fontLoader.drawText3x5(renderer, leds, pB, px, 7, 0, 150, 255);
        int sx = 28, sy = 7;
        renderer.setPixel(leds, sx, sy, 0, 150, 255); renderer.setPixel(leds, sx+2, sy+1, 0, 150, 255);
        renderer.setPixel(leds, sx+1, sy+2, 0, 150, 255); renderer.setPixel(leds, sx, sy+3, 0, 150, 255);
        renderer.setPixel(leds, sx+2, sy+4, 0, 150, 255);
        const char* lbl = showT ? "AMNH" : "HOJE";
        fontLoader.drawText3x5(renderer, leds, lbl, 31 - getTextWidth(lbl), 13, 100, 100, 100);
    }
    int getDuration() override { return 60; }
};
