import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://uk.wikipedia.org"
LIST_URL = "https://uk.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D1%85%D1%96%D0%BC%D1%96%D1%87%D0%BD%D0%B8%D1%85_%D0%B5%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%82%D1%96%D0%B2"
OUTPUT_DIR = "images"
GALLERY_FILE = "gallery.json"

HEADERS = {
    "User-Agent": "ChemoElementScraper/1.0 (Educational research; contact: user@example.com) Python-requests"
}

def get_high_res_url(img_tag) -> str:
    srcset = img_tag.get("srcset")
    if srcset:
        parts = srcset.split(",")
        last_candidate = parts[-1].strip().split(" ")[0]
        url = last_candidate
    else:
        url = img_tag.get("src", "")

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = urljoin(BASE_URL, url)
    return url

def download_image(url: str, save_path: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"    [!] Помилка завантаження {url}: {e}")
    return False

def update_gallery_json():
    """Сканує папку images та оновлює gallery.json для вебдодатка"""
    manifest = {}
    if not os.path.exists(OUTPUT_DIR):
        return
    for z in range(1, 119):
        folder = os.path.join(OUTPUT_DIR, str(z))
        if os.path.exists(folder):
            exts = ('.jpg', '.jpeg', '.png', '.webp', '.svg')
            files = [f"images/{z}/{f}" for f in sorted(os.listdir(folder)) if f.lower().endswith(exts)]
            if files:
                manifest[str(z)] = files
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n[✓] {GALLERY_FILE} успішно оновлено!")

def scrape_wiki():
    if not os.path.exists(OUTPUT_DIR):
        print(f"[!] Папку '{OUTPUT_DIR}' не знайдено! Переконайтеся, що скрипт лежить поруч із нею.")
        return

    print(f"[*] Завантажуємо таблицю з Вікіпедії...")
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"[!] Помилка з'єднання: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        print("[!] Таблицю елементів не знайдено.")
        return

    rows = table.find_all("tr")[1:]
    print(f"[*] Опрацьовуємо {len(rows)} рядків елементів...\n")

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        z_text = cells[0].get_text(strip=True)
        z_match = re.search(r"\d+", z_text)
        if not z_match:
            continue
        z = int(z_match.group())

        # Перевіряємо чи існує цільова папка images/Z/
        target_dir = os.path.join(OUTPUT_DIR, str(z))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        name_link = cells[1].find("a")
        if not name_link or not name_link.get("href"):
            continue

        name = name_link.get_text(strip=True)
        element_page_url = urljoin(BASE_URL, name_link["href"])

        print(f"[{z:03d}] {name} -> папка: images/{z}/")

        try:
            elem_resp = requests.get(element_page_url, headers=HEADERS, timeout=15)
            if elem_resp.status_code != 200:
                continue

            elem_soup = BeautifulSoup(elem_resp.text, "html.parser")
            infobox = elem_soup.find("table", class_=re.compile(r"infobox|infobox_v2"))
            img_urls = []

            # 1. Шукаємо знімки з інфобоксу картки
            if infobox:
                for img in infobox.find_all("img"):
                    width = int(img.get("width", 0)) if str(img.get("width", "")).isdigit() else 0
                    if width >= 50 or "image" in str(img.get("class", [])):
                        high_res = get_high_res_url(img)
                        if high_res and high_res not in img_urls:
                            img_urls.append(high_res)

            # 2. Якщо в інфобоксі немає, шукаємо перші якісні фото зі статті
            if not img_urls:
                for img in elem_soup.find_all("img"):
                    width = int(img.get("width", 0)) if str(img.get("width", "")).isdigit() else 0
                    if width >= 120:
                        high_res = get_high_res_url(img)
                        if high_res and high_res not in img_urls:
                            img_urls.append(high_res)
                    if len(img_urls) >= 2:
                        break

            # 3. Завантажуємо в папку з префіксом wiki_
            for idx, img_url in enumerate(img_urls, start=1):
                clean_url = img_url.split("?")[0]
                ext = os.path.splitext(clean_url)[1].lower()
                if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
                    ext = ".jpg"

                filename = f"wiki_{idx}{ext}"
                save_path = os.path.join(target_dir, filename)

                if not os.path.exists(save_path):
                    if download_image(img_url, save_path):
                        print(f"    [+] Додано: {filename}")
                else:
                    print(f"    [=] Вже є: {filename}")

            time.sleep(0.2)

        except Exception as e:
            print(f"    [!] Помилка: {e}")

    # Оновлюємо маніфест
    update_gallery_json()
    print("\n[*] Завершено! Усі зображення додано у ваші папки.")

if __name__ == "__main__":
    scrape_wiki()
