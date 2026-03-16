#pragma once
#include "App.h"
#include <WiFiS3.h>
#include <ArduinoJson.h>
#include <NTPClient.h>

extern NTPClient timeClient;

class MTSApp : public App {
private:
    String times[3];
    int count = 0;
    unsigned long lastUpdate = 0;

public:
    void updateData() override {
        if (millis() - lastUpdate < 60000 && lastUpdate != 0) return; 

        WiFiClient client; // HTTP normal, nao SSL
        const char* host = "intranet.mts.pt";
        
        Serial.println("\n[MTS] >>> TESTE PORTA 80 (HTTP) <<<");
        
        if (client.connect(host, 80)) {
            Serial.println("[MTS] Conectado! A pedir JSON...");
            
            String payload = "line=6&stations=19&day_type=1&season=2";
            client.println("POST /api/search HTTP/1.1");
            client.print("Host: "); client.println(host);
            client.println("Content-Type: application/x-www-form-urlencoded");
            client.print("Content-Length: "); client.println(payload.length());
            client.println("Connection: close");
            client.println();
            client.print(payload);

            unsigned long timeout = millis();
            while (client.available() == 0) {
                if (millis() - timeout > 5000) { Serial.println("[MTS] Timeout!"); client.stop(); return; }
            }

            String status = client.readStringUntil('\r');
            Serial.print("[MTS] Resposta: "); Serial.println(status);

            if (status.indexOf("301") > 0 || status.indexOf("302") > 0) {
                Serial.println("[MTS] Erro: O servidor FORCA o uso de HTTPS. Standalone direto impossivel.");
            } else {
                // Parse se nao redirecionar
                while (client.connected()) { if (client.readStringUntil('\n') == "\r") break; }
                StaticJsonDocument<128> filter;
                filter["data"]["times"][0]["start_time"] = true;
                DynamicJsonDocument doc(4096);
                if (deserializeJson(doc, client, DeserializationOption::Filter(filter)) == DeserializationError::Ok) {
                    long nowSecs = (long)timeClient.getHours() * 3600 + (long)timeClient.getMinutes() * 60 + (long)timeClient.getSeconds();
                    JsonArray arr = doc["data"]["times"];
                    count = 0;
                    for (JsonObject v : arr) {
                        long t = v["start_time"].as<String>().toInt();
                        if (t > nowSecs && count < 3) {
                            char buf[6]; sprintf(buf, "%02ld:%02ld", t / 3600, (t % 3600) / 60);
                            times[count++] = String(buf);
                        }
                    }
                    lastUpdate = millis();
                }
            }
            client.stop();
        } else {
            Serial.println("[MTS] Falha ao conectar na porta 80.");
        }
    }

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        renderer.clear(leds);
        fontLoader.drawText3x5(renderer, leds, "MTS", 1, 7, 0, 120, 255);
        if (count == 0) {
            fontLoader.drawText3x5(renderer, leds, "OFF", 14, 7, 255, 0, 0);
        } else {
            for (int i = 0; i < count; i++) {
                fontLoader.drawText3x5(renderer, leds, times[i].c_str(), 14, 1 + (i * 6), 255, 255, 255);
            }
        }
    }

    int getDuration() override { return 10; }
};
