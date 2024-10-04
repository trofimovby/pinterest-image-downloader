import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# Функция для загрузки изображений с Pinterest
def download_photos_from_pinterest(query, limit=3, output_dir="downloads"):
    # Настройка драйвера Selenium с опциями
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Формируем URL для поиска на Pinterest
    search_url = f"https://www.pinterest.com/search/pins/?q={query}"
    driver.get(search_url)
    time.sleep(5)  # Подождем, пока страница загрузится

    # Получаем HTML-код страницы
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Ищем все изображения
    images = soup.find_all('img')

    # Фильтруем URL изображений и ограничиваем до нужного количества
    image_urls = []
    for img in images:
        # Проверяем наличие srcset, который может содержать ссылки на более качественные изображения
        if img.get('srcset'):
            # Получаем список URL из srcset
            urls = img['srcset'].split(',')
            # Выбираем последний URL, который обычно будет наивысшего качества
            highest_quality_url = urls[-1].strip().split(' ')[0]
            image_urls.append(highest_quality_url)
        elif img.get('src'):
            image_urls.append(img['src'])

        if len(image_urls) >= limit:
            break

    # Проверка на случай, если не удалось получить достаточное количество изображений
    if not image_urls:
        print(f"Не удалось найти доступные изображения для запроса: {query}")
        driver.quit()
        return

    # Создаем папку для сохранения изображений, если её нет
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Скачиваем изображения
    for idx, img_url in enumerate(image_urls):
        try:
            print(f"Попытка скачать изображение {idx + 1}: {img_url}")  # Отладочная информация
            img_data = requests.get(img_url).content

            # Проверка на успешный ответ
            if img_data:
                with open(os.path.join(output_dir, f"{query}_{idx + 1}.jpg"), 'wb') as handler:
                    handler.write(img_data)
                print(f"Фото {idx + 1} по запросу '{query}' сохранено в лучшем качестве.")
            else:
                print(f"Ошибка: не удалось получить данные изображения {idx + 1}.")

        except Exception as e:
            print(f"Не удалось скачать фото {idx + 1}: {e}")

    # Закрываем браузер
    driver.quit()


# Чтение запросов из файла
def read_queries_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        queries = [line.strip() for line in file.readlines()]
    return queries


# Основная программа
if __name__ == '__main__':
    queries_file = "queries.txt"  # Файл с запросами

    # Проверка, существует ли файл с запросами
    if os.path.exists(queries_file):
        # Чтение всех запросов из файла
        queries = read_queries_from_file(queries_file)

        # Для каждого запроса загружаем изображения
        for query in queries:
            print(f"Загружаю фотографии по запросу: {query}")
            download_photos_from_pinterest(query)
            time.sleep(2)  # Задержка для предотвращения блокировок

    else:
        print(f"Файл {queries_file} не найден.")
