#!/usr/bin/env python3
import os
import json
import time
import urllib.request
from bs4 import BeautifulSoup

BASE_URL = "https://images-of-elements.com"
OUTPUT_DIR = "images"
GALLERY_FILE = "gallery.json"

ELEMENT_SLUGS = {
    1: "hydrogen", 2: "helium", 3: "lithium", 4: "beryllium", 5: "boron",
    6: "carbon", 7: "nitrogen", 8: "oxygen", 9: "fluorine", 10: "neon",
    11: "sodium", 12: "magnesium", 13: "aluminium", 14: "silicon", 15: "phosphorus",
    16: "sulfur", 17: "chlorine", 18: "argon", 19: "potassium", 20: "calcium",
    21: "scandium", 22: "titanium", 23: "vanadium", 24: "chromium", 25: "manganese",
    26: "iron", 27: "cobalt", 28: "nickel", 29: "copper", 30: "zinc",
    31: "gallium", 32: "germanium", 33: "arsenic", 34: "selenium", 35: "bromine",
    36: "krypton", 37: "rubidium", 38: "strontium", 39: "yttrium", 40: "zirconium",
    41: "niobium", 42: "molybdenum", 43: "technetium", 44: "ruthenium", 45: "rhodium",
    46: "palladium", 47: "silver", 48: "cadmium", 49: "indium", 50: "tin",
    51: "antimony", 52: "tellurium", 53: "iodine", 54: "xenon", 55: "caesium",
    56: "barium", 57: "lanthanum", 58: "cerium", 59: "praseodymium", 60: "neodymium",
    61: "promethium", 62: "samarium", 63: "europium", 64: "gadolinium", 65: "terbium",
    66: "dysprosium", 67: "holmium", 68: "erbium", 69: "thulium", 70: "ytterbium",
    71: "lutetium", 72: "hafnium", 73: "tantalum", 74: "tungsten", 75: "rhenium",
    76: "osmium", 77: "iridium", 78: "platinum", 79: "gold", 80: "mercury",
    81: "thallium", 82: "lead", 83: "bismuth", 84: "polonium", 85: "astatine",
    86: "radon", 87: "francium", 88: "radium", 89: "actinium", 90: "thorium",
    91: "protactinium", 92: "uranium", 93: "neptunium", 94: "plutonium", 95: "americium",
    96: "curium", 97: "berkelium", 98: "californium", 99: "einsteinium", 100: "fermium",
    101: "mendelevium", 102: "nobelium", 103: "lawrencium", 104: "rutherfordium",
    105: "dubnium", 106: "seaborgium", 107: "bohrium", 108: "hassium", 109: "meitnerium",
    110: "darmstadtium", 111: "roentgenium", 112: "copernicium", 113: "nihonium",
    114: "flerovium", 115: "moscovium", 116: "livermorium", 117: "tennessine", 118: "oganesson"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def download_file(url, filepath):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp, open(filepath, 'wb') as f:
            f.write(resp.read())
        return True
    except Exception:
        return False

def scan_local_gallery():
    manifest = {}
    if not os.path.exists(OUTPUT_DIR):
        return manifest
    for z in range(1, 119):
        folder = os.path.join(OUTPUT_DIR, str(z))
        if os.path.exists(folder):
            exts = ('.jpg', '.jpeg', '.png', '.webp', '.svg')
            files = [f"images/{z}/{f}" for f in sorted(os.listdir(folder)) if f.lower().endswith(exts)]
            if files:
                manifest[str(z)] = files
    return manifest

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("🚀 Починаємо завантаження зразків та фотографій...")

    for z, slug in ELEMENT_SLUGS.items():
        elem_dir = os.path.join(OUTPUT_DIR, str(z))
        os.makedirs(elem_dir, exist_ok=True)

        # 1. Головне зображення
        main_path = os.path.join(elem_dir, "main.jpg")
        if not os.path.exists(main_path):
            download_file(f"{BASE_URL}/{slug}.jpg", main_path)

        # 2. Додаткові зображення зі сторінки
        try:
            req = urllib.request.Request(f"{BASE_URL}/{slug}.html", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode('utf-8', errors='ignore'), 'html.parser')
                idx = 1
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if src and not src.startswith(('http', '/')) and src.endswith(('.jpg', '.png')):
                        extra_path = os.path.join(elem_dir, f"extra_{idx}.jpg")
                        if not os.path.exists(extra_path):
                            if download_file(f"{BASE_URL}/{src}", extra_path):
                                idx += 1
        except Exception:
            pass
        time.sleep(0.08)

    manifest = scan_local_gallery()
    with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово! Створено {GALLERY_FILE}")

if __name__ == "__main__":
    main()