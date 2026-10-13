import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

BASE_URL = "https://uk.wikipedia.org"
LIST_URL = "https://uk.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D1%85%D1%96%D0%BC%D1%96%D1%87%D0%BD%D0%B8%D1%85_%D0%B5%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%82%D1%96%D0%B2"
OUTPUT_DIR = "images"

HEADERS = {
    "User-Agent": "ChemoElementScraper/1.0 (Educational research; contact: user@example.com) Python-requests"
}

def clean_filename(name: str) -> str:
    """Видаляє заборонені символи для файлової системи."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_high_res_url(img_tag) -> str:
    """
    Отримує посилання на повнорозмірне або високоякісне зображення
    з атрибутів srcset або src Вікіпедії.
    """
    srcset = img_tag.get("srcset")
    if srcset:
        # Беремо найбільший варіант (зазвичай 2x або останній у списку)
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
    """Завантажує файл за посиланням та зберігає на диск."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"    [!] Помилка завантаження {url}: {e}")
    return False

def scrape_elements():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[*] Завантажуємо таблицю елементів з {LIST_URL}...")

    resp = requests.get(LIST_URL, headers=HEADERS)
    if resp.status_code != 200:
        print(f"[!] Не вдалося відкрити сторінку списку: HTTP {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        print("[!] Не знайдено таблицю елементів (wikitable).")
        return

    rows = table.find_all("tr")[1:]  # Пропускаємо рядок заголовків
    print(f"[*] Знайдено {len(rows)} рядків у таблиці. Починаємо обробку...\n")

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        # Зчитуємо атомний номер (Z), назву та символ
        z_text = cells[0].get_text(strip=True)
        z_match = re.search(r"\d+", z_text)
        if not z_match:
            continue
        z = int(z_match.group())

        # Посилання на окрему статтю елемента
        name_link = cells[1].find("a")
        if not name_link or not name_link.get("href"):
            continue

        name = clean_filename(name_link.get_text(strip=True))
        element_page_url = urljoin(BASE_URL, name_link["href"])

        # Створюємо персональну папку елемента (наприклад, "images/1_Гідроген")
        folder_name = f"{z}_{name}"
        elem_dir = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(elem_dir, exist_ok=True)

        print(f"[{z:03d}] {name} -> Відкриваємо статтю...")

        try:
            elem_resp = requests.get(element_page_url, headers=HEADERS, timeout=15)
            if elem_resp.status_code != 200:
                print(f"    [!] Пропущено (HTTP {elem_resp.status_code})")
                continue

            elem_soup = BeautifulSoup(elem_resp.text, "html.parser")

            # Знаходимо головний інфобокс картки елемента
            infobox = elem_soup.find("table", class_=re.compile(r"infobox|infobox_v2"))
            img_urls = []

            if infobox:
                # Шукаємо всі фотографії в інфобоксі
                for img in infobox.find_all("img"):
                    # Фільтруємо дрібні іконки та значки (наприклад, прапори, стрілочки тощо)
                    width = int(img.get("width", 0)) if str(img.get("width", "")).isdigit() else 0
                    if width >= 50 or "image" in str(img.get("class", [])):
                        high_res = get_high_res_url(img)
                        if high_res and high_res not in img_urls:
                            img_urls.append(high_res)

            # Якщо в інфобоксі фото не знайдено — беремо перші релевантні зображення з тіла статті
            if not img_urls:
                for img in elem_soup.find_all("img"):
                    width = int(img.get("width", 0)) if str(img.get("width", "")).isdigit() else 0
                    if width >= 120:
                        high_res = get_high_res_url(img)
                        if high_res and high_res not in img_urls:
                            img_urls.append(high_res)
                    if len(img_urls) >= 2:
                        break

            # Завантажуємо знайдені фото у папку
            if not img_urls:
                print("    [-] Зображень зразка не виявлено (синтетичний елемент або відсутнє фото).")
            else:
                for idx, img_url in enumerate(img_urls, start=1):
                    # Визначаємо розширення файлу (.jpg, .png тощо)
                    clean_url = img_url.split("?")[0]
                    ext = os.path.splitext(clean_url)[1].lower()
                    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
                        ext = ".jpg"

                    save_file_path = os.path.join(elem_dir, f"sample_{idx}{ext}")
                    
                    if not os.path.exists(save_file_path):
                        success = download_image(img_url, save_file_path)
                        if success:
                            print(f"    [+] Завантажено: sample_{idx}{ext}")
                    else:
                        print(f"    [=] Файл sample_{idx}{ext} вже існує.")

            # Ввічлива затримка між запитами до серверів Вікіпедії
            time.sleep(0.3)

        except Exception as e:
            print(f"    [!] Помилка обробки елемента {name}: {e}")

    print("\n[*] Завантаження завершено! Усі зображення збережено в папку 'images/'.")

if __name__ == "__main__":
    scrape_elements()