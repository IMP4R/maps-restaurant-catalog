import importlib
import sys
import subprocess

def check_and_install_libraries():
    libraries = ["selenium", "bs4"]
    
    missing_libs = []
    for lib in libraries:
        try:
            importlib.import_module(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if not missing_libs:
        return True
        
    print(f"Необходимо установить: {', '.join(missing_libs)}")
    
    methods = [
        [sys.executable, "-m", "pip", "install", "--user"],
        [sys.executable, "-m", "pip", "install", "--break-system-packages"],
    ]
    
    for method in methods:
        try:
            print(f"Пробуем установить: {' '.join(method)} {' '.join(missing_libs)}")
            result = subprocess.run(
                method + missing_libs,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("Установка успешна")
                return True
            else:
                print(f"Метод не сработал: {result.stderr}")
                
        except Exception as e:
            print(f"Ошибка: {e}")
    
    print("Не удалось установить библиотеки автоматически")
    print("Выполните вручную:")
    print(f"{sys.executable} -m pip install --user {' '.join(missing_libs)}")
    return False
if not check_and_install_libraries():
    sys.exit(1)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import time
import random
from bs4 import BeautifulSoup
from collections import namedtuple
from Restaurant_db import RestaurantDB
from Restaurant_db import Restaurant
from Save_photo import download_image
import re
import requests
import json


def get_first_integer(text):
        if not text or not isinstance(text, str):
            return 0
        
        match = re.search(r'-?\d+', text)
        return int(match.group()) if match else 0

class SiteParser:
    def __init__(self, headless=True, db_file="restaurantsYaMaps.json"):
        self.setup_driver(headless)
        self.db = RestaurantDB()
        self.db_file = db_file
        self.db.load_from_file(db_file)
        print(f"Загружено {len(self.db)} ресторанов c бд")
        
    def setup_driver(self, headless):
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.1 Safari/537.36")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def scroll_in_container(self, container_selector, scrolls_per_pause=5):
        try:
            scroll_container = self.driver.find_element(By.CSS_SELECTOR, container_selector)
            
        except NoSuchElementException:
            print(f"Контейнер {container_selector} не найден")
            return False
            
        for i in range(scrolls_per_pause):
            scroll_amount = random.randint(10000, 11000)
            
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[1];", 
                scroll_container, 
                scroll_amount
            )
            time.sleep(random.uniform(0.1, 0.3))
            
        
        return True
        
    def parse_site(self, url, target_selector=".search-snippet-view", container_selector=".scroll__container", stop_selector='.add-business-view', _type='Ресторан'):
        try:
            print("Загрузка сайта...")
            self.driver.get(url)
            if "captcha" in self.driver.current_url or "checkcaptcha" in self.driver.current_url:
                        print("Обнаружена капча!")
                        time.sleep(18)
            time.sleep(2)
            print("Сайт загружен")
            print(f"Парсим...")
            for i in range(100):
                self.scroll_in_container(container_selector)
                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')
                if len(soup.select(stop_selector))>0: break             
                
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            items = soup.select(target_selector)
            items_list = list(items)
            restaurants = []
            
            for item in items_list:
                
                id_elem = item.select_one('[data-id]')
                _id = id_elem.get('data-id', '') if id_elem else ''
                
                title = item.select_one('.search-business-snippet-view__title')
                address = item.select_one('.search-business-snippet-view__address')
                #photos = item.select('.search-business-snippet-view__gallery img')
                price = item.select_one('.search-business-snippet-subtitle-view__description')
                
                if title and address:
                    _title = title.get_text(strip=True) if hasattr(title, 'get_text') else str(title)
                    _address = address.get_text(strip=True) if hasattr(address, 'get_text') else str(address)
                    
                    _photo_url = ""
                    _photo_path = ""
                    #for photo in photos:
                    #    src = photo.get('src', '')
                    #    if 'M_height' in src:
                    #        _photo_url = src
                    #        _photo_path = download_image(_photo_url.replace('M_height', 'orig'))
                    #        if _photo_path!="": break 
                    
                    _pricet = price.get_text(strip=True) if price and hasattr(price, 'get_text') else str(price) if price else ""
                    _price = get_first_integer(str(_pricet)) if _pricet else 0
                    _category = "Дорого" if _price > 2000 else "Средне" if _price > 1000 else "Бюджетно"
                    _number = "none"
                    _times = ["none","none","none","none","none","none","none"]
                    _coord = ""
                    _raiting = ""
                    
                    restaurants.append(Restaurant(_id, _title, _address, _photo_url, _photo_path, _coord, _raiting, _type, _category, _number, _times[0], _times[1], _times[2], _times[3], _times[4], _times[5], _times[6]))

            added_count = self.db.add_batch(restaurants)

            self.db.save_to_file(self.db_file)

            print(f"Найдено: {len(restaurants)}, Новых: {added_count}, Всего: {len(self.db)}")
                    
            return added_count

        except Exception as e:
            print(f"Ошибка: {e}")
            return 0

    def parse_site_add(self, db_file=None):
        if db_file is None:
            db_file = self.db_file
        
        try:
            print("Загрузка данных из JSON...")
            self.db.load_from_file(db_file)
            
            restaurants_to_update = []
            updated_count = 0
            
            for restaurant in self.db.data:
                if restaurant.number != "none" and restaurant.mo != "none" and restaurant.photo_path != "":
                    continue
                    
                print(f"Парсим дополнительную информацию для: {restaurant.title}")
                
                org_url = f"https://yandex.ru/maps/org/{restaurant.urlid}/"
                
                try:
                    self.driver.get(org_url)
                    time.sleep(1)
                    
                    if "captcha" in self.driver.current_url or "checkcaptcha" in self.driver.current_url:
                        print("Обнаружена капча!")
                        time.sleep(20)
                    
                    page_html = self.driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')
                    
                    
                    _number = "none"
                    phone_element = soup.select_one('.card-phones-view__phone-number span[itemprop="telephone"]')
                    if not phone_element:
                        phone_element = soup.select_one('[class*="phone"]')
                        phone_element = soup.select_one('.business-contacts-view__phone')
                    
                    if phone_element:
                        _number = phone_element.get_text(strip=True)
                        print(f"Найден телефон: {_number}")
                    
                    _times = ["none"] * 7
                    time_meta_tags = soup.select('meta[itemprop="openingHours"]')
                    
                    days_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                    for meta_tag in time_meta_tags:
                        content = meta_tag.get('content', '')
                        day_code = content[:2]
                        time_range = content[3:]
                        
                        if day_code in days_order:
                            day_index = days_order.index(day_code)
                            _times[day_index] = time_range
                            #print(f"Найдено время для {day_code}: {time_range}")
                    
                    if all(time == "none" for time in _times):
                        time_elements = soup.select('[class*="schedule"]')
                        for i, elem in enumerate(time_elements[:7]):
                            time_text = elem.get_text(strip=True)
                            if time_text:
                                _times[i] = time_text
                    
                    restaurant.number = _number
                    restaurant.mo = _times[0]
                    restaurant.tu = _times[1]
                    restaurant.we = _times[2]
                    restaurant.th = _times[3]
                    restaurant.fr = _times[4]
                    restaurant.sa = _times[5]
                    restaurant.su = _times[6]

                    if restaurant.photo_url == "":
                        print(f"Обновляем фото...")
                        photos = soup.select_one('.carousel__content').select('.img-with-alt img')
                        _photo_url = ""
                        _photo_path = ""
                        print(f"Найдено {len(photos)} фото")
                        for photo in photos:
                            src = photo.get('src', '')
                            _photo_url = src
                            _photo_path = download_image(_photo_url.replace('XXL_height', 'orig'))
                            restaurant.photo_url = _photo_url
                            restaurant.photo_path = _photo_path
                            print(f"Фото обновлено: {_photo_path}")
                            if _photo_path!="": break 
                    
                    restaurants_to_update.append(restaurant)
                    updated_count += 1
                    
                    print(f"Обновлено: {restaurant.title}")
                    
                except Exception as e:
                    print(f"Ошибка при парсинге {restaurant.title}: {e}")
                    continue
            
            if restaurants_to_update:
                self.db.save_to_file(db_file)
                print(f"Обновлено ресторанов: {updated_count}")
            else:
                print("Нет ресторанов для обновления")
                
            return updated_count
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def close(self):
        self.driver.quit()

print("Запуск парсера...")
if __name__ == "__main__":
    parser = SiteParser(headless=False)
    _url = "https://yandex.ru/maps/55/tyumen/search"
    try:
        for i in range(5):
            break
            results = parser.parse_site(
                url=_url+"/Рестораны/",
                _type = 'Ресторан'
            )
            results = parser.parse_site(
                url=_url+"/Кофейни/",
                _type = 'Кофейня'
            )
            results = parser.parse_site(
                url=_url+"/Быстрое%20питание/",
                _type = 'Фастфуд'
            )
            results = parser.parse_site(
                url=_url+"/Кафе/",
                _type = 'Кафе'
            )
            results = parser.parse_site(
                url=_url+"/Бары/",
                _type = 'Бар'
            )

        #for i in range(5): results = parser.parse_site(url=_url+"/Где%20поесть/", _type = '/Где%20поесть/')
        parser.parse_site_add()

    finally:
        parser.close()
        input("Enter для выхода...")