#pragma once
#include "Renderer.h"
#include "FontLoader.h"
#include <FastLED.h>
#include <LEDMatrix.h>

class App {
public:
    virtual void updateData() {}
    virtual void draw(Renderer& renderer, cLEDMatrixBase& leds, FontLoader& fontLoader) = 0;
    virtual int getDuration() = 0; 
    virtual void resetApp() {} // Para limpar timers ao iniciar
    virtual ~App() {}
};
