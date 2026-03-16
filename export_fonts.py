import os
import cv2

def escape_char(c):
    if c == "COLON": return "COLON_CHAR"
    if c.isdigit(): return "NUM_" + c
    return c

out = open("esp32_dashboard/Fonts.h", "w", encoding="utf-8")
out.write("#pragma once\n")
out.write("#include <Arduino.h>\n\n")

def process_font(size_name, folder):
    if not os.path.exists(folder): return
    out.write(f"// Font {size_name}\n")
    chars_list = []
    
    files = sorted([f for f in os.listdir(folder) if f.endswith(".bmp")])
    
    for file in files:
        raw_name = file.split(".")[0].upper()
        c_name = escape_char(raw_name)
        var_name = f"font_{size_name}_{c_name}"
        
        img = cv2.imread(os.path.join(folder, file), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            h, w = binary.shape
            chars_list.append((raw_name, var_name, w, h))
            
            out.write(f"const uint8_t {var_name}[] = {{\n")
            bytes_list = []
            for y in range(h):
                for x in range(w):
                    # REVERTIDO: O pixel é claro (branco) na imagem original, queremos 1 aqui para desenhar
                    bytes_list.append("1" if binary[y,x] > 127 else "0")
            out.write("  " + ", ".join(bytes_list) + "\n};\n\n")

    out.write(f"struct FontChar_{size_name} {{\n")
    out.write("  char name;\n")
    out.write("  const uint8_t* data;\n")
    out.write("  uint8_t width;\n")
    out.write("  uint8_t height;\n")
    out.write("};\n\n")

    out.write(f"const FontChar_{size_name} map_{size_name}[] = {{\n")
    for raw, var, w, h in chars_list:
        ch = f"'{raw}'" if len(raw) == 1 else ("':'" if raw == "COLON" else "'?'")
        out.write(f"  {{{ch}, {var}, {w}, {h}}},\n")
    out.write("};\n")
    out.write(f"const size_t map_{size_name}_size = sizeof(map_{size_name}) / sizeof(map_{size_name}[0]);\n\n")

def process_weather():
    folder = "fonts/weather"
    if not os.path.exists(folder): return
    out.write(f"// Weather Icons\n")
    
    icons_list = []
    files = sorted([f for f in os.listdir(folder) if f.endswith(".bmp")])
    
    for file in files:
        raw_name = file.split(".")[0].upper()
        var_name = f"icon_weather_{raw_name}"
        
        img = cv2.imread(os.path.join(folder, file), cv2.IMREAD_UNCHANGED)
        if img is not None:
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            elif len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
                    
            h, w, c = img.shape
            icons_list.append((raw_name, var_name, w, h))
            
            out.write(f"const uint8_t {var_name}[] = {{\n")
            for y in range(h):
                row_bytes = []
                for x in range(w):
                    px = img[y,x]
                    row_bytes.append(f"{px[0]}, {px[1]}, {px[2]}, {px[3]}")
                out.write("  " + ", ".join(row_bytes) + ("," if y < h-1 else "") + "\n")
            out.write("};\n\n")

    out.write(f"struct WeatherIcon {{\n")
    out.write("  const char* name;\n")
    out.write("  const uint8_t* data;\n")
    out.write("  uint8_t width;\n")
    out.write("  uint8_t height;\n")
    out.write("};\n\n")

    out.write(f"const WeatherIcon map_weather[] = {{\n")
    for raw, var, w, h in icons_list:
        out.write(f"  {{\"{raw}\", {var}, {w}, {h}}},\n")
    out.write("};\n")
    out.write(f"const size_t map_weather_size = sizeof(map_weather) / sizeof(map_weather[0]);\n\n")

process_font("3x5", "fonts/3x5")
process_font("5x9", "fonts/5x9")
process_weather()
out.close()
print("Fonts exported successfully (NORMAL) to esp32_dashboard/Fonts.h")
