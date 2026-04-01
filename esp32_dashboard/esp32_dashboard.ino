#include <WiFiS3.h>
#include <RTC.h>
#include <FastLED.h>
#include <LEDMatrix.h>
#include <time.h>

#include "Renderer.h"
#include "FontLoader.h"
#include "App.h"
#include "ClockApp.h"
#include "WeatherApp.h"

// --- Configurações WiFi ---
const char* ssid = "NEEC_2G";
const char* password = "neecfct!";

// --- Fuso Horário de Lisboa (Automático Verão/Inverno) ---
const char* TZ_INFO = "WET0WEST,M3.5.0/1,M10.5.0/2";

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

const int CYCLE_COUNT = 2;
const int cycle_durations[] = {300, 60}; 
const int app_indices[] = {0, 1}; 

App* available_apps[2];
int current_cycle_idx = 0;
unsigned long cycle_start_time = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    // Inicialização da Matriz
    FastLED.addLeds<CHIPSET, LED_PIN, COLOR_ORDER>(leds[0], MATRIX_WIDTH * MATRIX_HEIGHT).setCorrection(TypicalLEDStrip);
    FastLED.setBrightness(127);
    FastLED.clear(true);
    FastLED.show();

    // Conexão WiFi com timeout
    Serial.print("A conectar ao WiFi");
    WiFi.begin(ssid, password);
    int auth_timeout = 0;
    while (WiFi.status() != WL_CONNECTED && auth_timeout < 20) { 
        delay(500); 
        Serial.print(".");
        auth_timeout++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi Conectado!");
        RTC.begin();
        setenv("TZ", TZ_INFO, 1);
        tzset();

        // Tentar obter a hora várias vezes
        unsigned long unixTime = 0;
        int retry = 0;
        while (unixTime < 1600000000 && retry < 15) { // 1600... é um timestamp de 2020
            Serial.println("A tentar obter hora do NTP...");
            unixTime = WiFi.getTime(); 
            if (unixTime == 0) {
                delay(2000); // Espera 2 segundos entre tentativas
                retry++;
            }
        }

        if (unixTime > 0) {
            RTCTime startTime(unixTime);
            RTC.setTime(startTime);
            Serial.println("Hora configurada no RTC!");
        }
    } else {
        Serial.println("\nFalha ao ligar ao WiFi.");
    }

    available_apps[0] = new ClockApp();
    available_apps[1] = new WeatherApp();
    cycle_start_time = millis();
}

void loop() {
    int current_app_idx = app_indices[current_cycle_idx];
    App* current_app = available_apps[current_app_idx];

    // Renderiza a aplicação
    current_app->draw(renderer, leds, fontLoader);

    // Teu ajuste manual de cores para as primeiras colunas
    for (int x = 0; x < 13; x++) {
        CRGB c = leds(x, 0); 
        leds(x, 0) = CRGB(c.g, c.r, c.b);
    }
    FastLED.show();

    // Lógica de troca de ciclo
    unsigned long elapsed = (millis() - cycle_start_time) / 1000;
    if (elapsed >= (unsigned long)cycle_durations[current_cycle_idx]) {
        current_cycle_idx = (current_cycle_idx + 1) % CYCLE_COUNT;
        cycle_start_time = millis();
        
        available_apps[app_indices[current_cycle_idx]]->updateData();
        available_apps[app_indices[current_cycle_idx]]->resetApp();
    }

    delay(50);
}