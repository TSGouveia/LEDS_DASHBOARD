from apps.weather_app import WeatherApp
from fonts import FontLoader

class MockFontLoader:
    def draw_bitmap(self, *args, **kwargs): pass
    def draw_text(self, *args, **kwargs): pass

def test_weather():
    app = WeatherApp("Test", MockFontLoader())
    print("Starting Weather Update...")
    app.update_data()
    print("\nUpdate finished.")

if __name__ == "__main__":
    test_weather()
