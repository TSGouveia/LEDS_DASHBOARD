#pragma once
#include "App.h"
#include <WiFiS3.h>
#include <ArduinoJson.h>

class FootballApp : public App {
private:
    struct Game { String home; String away; String score; String status; };
    Game games[2];
    int count = 0;
    unsigned long lastUpdate = 0;
    const char* token = "89a4b73251c44a309c0d5d06c648d461";

public:
    void updateData() override {
        if (millis() - lastUpdate < 300000 && lastUpdate != 0) return;

        WiFiSSLClient client;
        Serial.println("\n[Football] A tentar ligar a api.football-data.org...");

        if (client.connect("api.football-data.org", 443)) {
            Serial.println("[Football] Conectado!");
            client.println("GET /v4/matches HTTP/1.1");
            client.println("Host: api.football-data.org");
            client.print("X-Auth-Token: "); client.println(token);
            client.println("Connection: close");
            client.println();

            unsigned long timeout = millis();
            while (client.connected() && !client.available()) {
                if (millis() - timeout > 10000) break;
            }

            while (client.connected()) {
                if (client.readStringUntil('\n') == "\r") break;
            }

            // Filtro para os campos do Benfica, Porto, Sporting, Portugal
            StaticJsonDocument<256> filter;
            filter["matches"][0]["homeTeam"]["tla"] = true;
            filter["matches"][0]["homeTeam"]["id"] = true;
            filter["matches"][0]["awayTeam"]["tla"] = true;
            filter["matches"][0]["awayTeam"]["id"] = true;
            filter["matches"][0]["score"]["fullTime"]["home"] = true;
            filter["matches"][0]["score"]["fullTime"]["away"] = true;
            filter["matches"][0]["status"] = true;

            DynamicJsonDocument doc(8192);
            deserializeJson(doc, client, DeserializationOption::Filter(filter));

            JsonArray matches = doc["matches"];
            count = 0;
            for (JsonObject m : matches) {
                int hId = m["homeTeam"]["id"];
                int aId = m["awayTeam"]["id"];
                
                // IDs: 503 (Porto), 1903 (Benfica), 498 (Sporting), 765 (Portugal)
                if (hId == 503 || hId == 1903 || hId == 498 || hId == 765 ||
                    aId == 503 || aId == 1903 || aId == 498 || aId == 765) {
                    
                    if (count < 2) {
                        games[count].home = m["homeTeam"]["tla"].as<String>();
                        games[count].away = m["awayTeam"]["tla"].as<String>();
                        int hS = m["score"]["fullTime"]["home"] | 0;
                        int aS = m["score"]["fullTime"]["away"] | 0;
                        games[count].score = String(hS) + "-" + String(aS);
                        games[count].status = m["status"].as<String>();
                        count++;
                    }
                }
            }
            lastUpdate = millis();
            client.stop();
        } else {
            Serial.println("[Football] Falha na ligacao HTTPS.");
        }
    }

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        renderer.clear(leds);
        if (count == 0) {
            fontLoader.drawText3x5(renderer, leds, "NO GAMES", 2, 7, 100, 100, 100);
            return;
        }
        for (int i = 0; i < count; i++) {
            int y = (i == 0) ? 1 : 10;
            fontLoader.drawText3x5(renderer, leds, games[i].home.c_str(), 1, y, 255, 255, 255);
            fontLoader.drawText3x5(renderer, leds, games[i].score.c_str(), 13, y, 255, 255, 0);
            fontLoader.drawText3x5(renderer, leds, games[i].away.c_str(), 23, y, 255, 255, 255);
        }
    }

    int getDuration() override { return 10; }
};
