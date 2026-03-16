#include <WiFiS3.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <FastLED.h>
#include <LEDMatrix.h>

#include "Renderer.h"
#include "FontLoader.h"
#include "App.h"
#include "ClockApp.h"
#include "WeatherApp.h"

// --- Configurações WiFi ---
const char* ssid = "NEEC_2G";
const char* password = "neecfct!";

// --- Configurações da Matriz ---
#define LED_PIN 10
#define COLOR_ORDER RGB
#define CHIPSET WS2812B
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 18
#define MATRIX_TYPE HORIZONTAL_MATRIX

// --- Instâncias Globais ---
Renderer renderer(MATRIX_WIDTH, MATRIX_HEIGHT);
FontLoader fontLoader;
cLEDMatrix<MATRIX_WIDTH, MATRIX_HEIGHT, MATRIX_TYPE> leds;

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0); 

// Novo ciclo: 0=Clock (5m), 1=Weather (1m)
const int CYCLE_COUNT = 2;
const int cycle_durations[] = {300, 60}; 
const int app_indices[] = {0, 1}; 

App* available_apps[2];
int current_cycle_idx = 0;
unsigned long cycle_start_time = 0;

void setup() {
    Serial.begin(115200);
    FastLED.addLeds<CHIPSET, LED_PIN, COLOR_ORDER>(leds[0], MATRIX_WIDTH * MATRIX_HEIGHT).setCorrection(TypicalLEDStrip);
    FastLED.setBrightness(127);
    FastLED.clear(true);
    FastLED.show();

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }

    timeClient.begin();
    while(!timeClient.update()) { timeClient.forceUpdate(); delay(1000); }

    available_apps[0] = new ClockApp();
    available_apps[1] = new WeatherApp();
    
    cycle_start_time = millis();
}

void loop() {
    timeClient.update();
    
    int current_app_idx = app_indices[current_cycle_idx];
    App* current_app = available_apps[current_app_idx];

    current_app->draw(renderer, leds, fontLoader);

    for (int x = 0; x < 13; x++) {
        CRGB c = leds(x, 0); 
        leds(x, 0) = CRGB(c.g, c.r, c.b);
    }
    FastLED.show();

    unsigned long elapsed = (millis() - cycle_start_time) / 1000;
    if (elapsed >= (unsigned long)cycle_durations[current_cycle_idx]) {
        current_cycle_idx = (current_cycle_idx + 1) % CYCLE_COUNT;
        cycle_start_time = millis();
        
        App* next_app = available_apps[app_indices[current_cycle_idx]];
        next_app->updateData();
        next_app->resetApp();
    }

    delay(50);
}
