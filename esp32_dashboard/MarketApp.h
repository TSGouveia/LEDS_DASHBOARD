#pragma once
#include "App.h"
#include <WiFiS3.h>

class MarketApp : public App {
private:
    float btc_pts[32];
    float sp_pts[32];
    float btc_now = 0, sp_now = 0;
    bool has_btc = false, has_sp = false;
    unsigned long lastUpdate = 0;
    unsigned long displayStartTime = 0;

    int getTextWidth(const char* text) {
        int len = strlen(text);
        return (len > 0) ? (len * 3) + (len - 1) : 0;
    }

    void drawGraph(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader, float* graph_pts, float now, const char* label, uint8_t r, uint8_t g, uint8_t b) {
        renderer.clear(leds);
        float minP = 9999999, maxP = -9999999;
        for(int i=0; i<32; i++) {
            if(graph_pts[i] <= 1.0) continue;
            if(graph_pts[i] < minP) minP = graph_pts[i];
            if(graph_pts[i] > maxP) maxP = graph_pts[i];
        }
        if (minP == 9999999) { minP = 0; maxP = 1; }
        float range = maxP - minP;
        if(range <= 0) range = 1.0;

        bool trendUp = (now >= graph_pts[0]);
        uint8_t lr = trendUp ? 0 : 255, lg = trendUp ? 255 : 0, lb = 0;
        uint8_t fr = lr / 10, fg = lg / 10, fb = lb / 10;

        for(int x=0; x<32; x++) {
            float val = graph_pts[x];
            if (val <= 1.0) val = minP;
            float norm = (val - minP) / range;
            int y_line = 17 - (int)(norm * 11); 
            for(int y_fill = y_line + 1; y_fill <= 17; y_fill++) renderer.setPixel(leds, x, y_fill, fr, fg, fb);
            renderer.setPixel(leds, x, y_line, lr, lg, lb);
        }

        fontLoader.drawText3x5(renderer, leds, label, 1, 1, 255, 255, 255);
        if(now > 1000) {
            int integers = (int)(now / 1000);
            int decimals = (int)((now / 1000.0 - integers) * 10);
            char intStr[8], decStr[8];
            sprintf(intStr, "%d", integers);
            sprintf(decStr, "%dk", decimals);
            int totalW = getTextWidth(intStr) + 3 + getTextWidth(decStr);
            int sx = 31 - totalW;
            fontLoader.drawText3x5(renderer, leds, intStr, sx, 1, 255, 255, 255);
            int dotX = sx + getTextWidth(intStr) + 1;
            renderer.setPixel(leds, dotX, 5, 255, 255, 255);
            fontLoader.drawText3x5(renderer, leds, decStr, dotX + 2, 1, 255, 255, 255);
        } else {
            char valStr[16]; sprintf(valStr, "%.0f", now);
            fontLoader.drawText3x5(renderer, leds, valStr, 31 - getTextWidth(valStr), 1, 255, 255, 255);
        }
    }

    void fetchBinance() {
        WiFiSSLClient client;
        if (client.connect("api.binance.com", 443)) {
            client.println("GET /api/v3/ticker/price?symbol=BTCEUR HTTP/1.1");
            client.println("Host: api.binance.com");
            client.println("Connection: close"); client.println();
            if (client.find("\"price\":\"")) btc_now = client.readStringUntil('\"').toFloat();
            client.stop();
        }
        if (client.connect("api.binance.com", 443)) {
            client.println("GET /api/v3/klines?symbol=BTCEUR&interval=4h&limit=32 HTTP/1.1");
            client.println("Host: api.binance.com");
            client.println("Connection: close"); client.println();
            unsigned long timeout = millis();
            while (client.connected() && !client.available() && (millis() - timeout < 5000));
            while (client.connected()) { if (client.readStringUntil('\n') == "\r") break; }
            int count = 0;
            if (client.find("[[")) {
                while(client.connected() && count < 32) {
                    for(int j=0; j<7; j++) client.find("\""); 
                    String p = client.readStringUntil('\"');
                    btc_pts[count++] = p.toFloat();
                    if (!client.findUntil("[", "]]")) break; 
                }
                has_btc = (count > 0);
            }
            client.stop();
        }
    }

    void fetchYahooSP() {
        WiFiSSLClient client;
        const char* host = "query1.finance.yahoo.com";
        if (client.connect(host, 443)) {
            client.println("GET /v8/finance/chart/%5EGSPC?interval=60m&range=5d HTTP/1.1");
            client.print("Host: "); client.println(host);
            client.println("User-Agent: Mozilla/5.0");
            client.println("Connection: close"); client.println();
            unsigned long timeout = millis();
            while (client.connected() && !client.available() && (millis() - timeout < 10000));
            while (client.connected()) { if (client.readStringUntil('\n') == "\r") break; }
            while (client.connected() && !has_sp) {
                String line = client.readStringUntil(',');
                if (line.indexOf("\"regularMarketPrice\":") != -1) {
                    sp_now = line.substring(line.indexOf(":") + 1).toFloat();
                }
                if (line.indexOf("\"open\":[") != -1) {
                    float rolling[32]; int totalFound = 0;
                    while (client.connected()) {
                        while (client.available() && (client.peek() == ' ' || client.peek() == 'n' || client.peek() == 'u' || client.peek() == 'l')) client.read();
                        String v = ""; while (client.available()) {
                            char c = client.read(); if (c == ',' || c == ']') break;
                            if ((c >= '0' && c <= '9') || c == '.') v += c;
                        }
                        if (v.length() > 0) { rolling[totalFound % 32] = v.toFloat(); totalFound++; }
                        if (v == "" && !client.available()) break;
                        if (client.peek() == ']') break;
                    }
                    if (totalFound > 0) {
                        for(int i=0; i<32; i++) sp_pts[i] = (totalFound < 32) ? rolling[i] : rolling[(totalFound + i) % 32];
                        has_sp = true;
                    }
                    break;
                }
            }
            client.stop();
        }
    }

public:
    void resetApp() override { displayStartTime = millis(); }

    void updateData() override {
        if (millis() - lastUpdate < 600000 && has_btc && has_sp) return; 
        fetchBinance();
        delay(500);
        fetchYahooSP();
        lastUpdate = millis();
    }

    void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) override {
        unsigned long elapsed = millis() - displayStartTime;
        if (elapsed < 30000 && has_btc) drawGraph(renderer, leds, fontLoader, btc_pts, btc_now, "BTC", 255, 150, 0);
        else if (has_sp) drawGraph(renderer, leds, fontLoader, sp_pts, sp_now, "SP", 0, 200, 255);
    }

    int getDuration() override { return 60; }
};
