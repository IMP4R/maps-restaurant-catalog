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
from selenium.webdriver.common.action_chains import ActionChains
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

def clean_phone_to_format(phone):
        if not phone:
            return None
        
        clean_digits = re.sub(r'[^\d+]', '', phone)

        if clean_digits.startswith('8'):
            clean_digits = '+7' + clean_digits[1:]

        elif len(clean_digits) == 10:
            clean_digits = '+7' + clean_digits

        elif clean_digits.startswith('7') and not clean_digits.startswith('+7'):
            clean_digits = '+' + clean_digits
        

        if len(clean_digits) == 12 and clean_digits.startswith('+7'):
            formatted = (f"+7 ({clean_digits[2:5]}) {clean_digits[5:8]}-{clean_digits[8:10]}-{clean_digits[10:12]}")
            return formatted
        else:
            return clean_digits


class SiteParser:
    def __init__(self, headless=True, db_file="restaurants2gis.json"):
        self.setup_driver(headless)
        self.db = RestaurantDB()
        self.db_file = db_file
        self.db.load_from_file(db_file)
        print(f"Загружено {len(self.db)} ресторанов c бд")
        
    def setup_driver(self, headless):
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.images": 2
        }
        options.add_experimental_option("prefs", prefs)
        
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
    
    def parse_items(self, items, _type='Ресторан'):
        restaurants = []
        for item in items:
            link = item.select_one('a._1rehek')
            href = link['href']
            id_match = re.search(r'firm/(\d+)', href)
            if id_match: org_id = id_match.group(1)
            _id = org_id
            
            title = item.select_one('._lvwrwt')
            address = item.select_one('._sfdp8cg')

            #photos = item.select('.search-business-snippet-view__gallery img')
            price = item.select_one('._4cxmw7')
            raiting = item.select_one('._y10azs')
            
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
                _category = "от 1500" if _price > 1500 else "400-1500" if _price > 400 else "до 400"
                _number = "none"
                _coord = ""
                _times = ""
                _raiting = raiting.get_text(strip=True) if raiting and hasattr(address, 'get_text') else str(raiting) if raiting else ""
                
                restaurants.append(Restaurant(_id, _title, _address, _photo_url, _photo_path, _coord, _raiting, _type, _category, _number, _times))

        added_count = self.db.add_batch(restaurants)

        self.db.save_to_file(self.db_file)

        print(f"Найдено: {len(restaurants)}, Новых: {added_count}, Всего: {len(self.db)}")

        return added_count

    def parse_site(self, url, stop_selector='.add-business-view', _type='Ресторан'):
        try:
            print("Загрузка сайта...")
            self.driver.get(url)
            if "captcha" in self.driver.current_url or "checkcaptcha" in self.driver.current_url:
                        print("Обнаружена капча!")
                        time.sleep(18)
            time.sleep(1)
            print("Сайт загружен")
            print(f"Парсим...")

            pi = 0
            past_address = 'first'
            address = 'second'
            for i in range(100):    
                time.sleep(0.1)
                while(address == past_address):
                    page_html = self.driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')
                    items = soup.select("._1kf6gff")
                    items_list = list(items)
                    address = items_list[0].select_one('._sfdp8cg')
                    time.sleep(0.01)
                
                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')
                items = soup.select("._1kf6gff")
                items_list = list(items)
                address = items_list[0].select_one('._sfdp8cg')
                pi += self.parse_items(items_list, _type)
                
                containers = self.driver.find_elements(By.CSS_SELECTOR, 'div._n5hmn94')
                if len(containers) > 1: container = containers[1]
                elif past_address == 'first' : container = containers[0]
                else: break
                past_address = address
                actions = ActionChains(self.driver)
                actions.move_to_element(container).click().perform()
   
            return pi

        except Exception as e:
            print(f"Ошибка: {e}")
            return 0

    def get_redirect_url(self, url, timeout=10):
        try:
            response = requests.get(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            return response.url
        except Exception as e:
            print(f"Ошибка при получении редиректа: {e}")
            return None

    def parse_site_add(self, db_file=None):
        if db_file is None:
            db_file = self.db_file
        
        try:
            print("Загрузка данных из JSON...")
            self.db.load_from_file(db_file)
            
            restaurants_to_update = []
            updated_count = 0
            
            for restaurant in self.db.data:
                if restaurant.number != "none" and restaurant.coord != "":
                    continue
                    
                print(f"Парсим дополнительную информацию для: {restaurant.title}")
                
                org_url = f"https://2gis.ru/tyumen/firm/{restaurant.urlid}/"
                
                try:
                    self.driver.get(org_url)
                    time.sleep(0.1)
                    
                    if "captcha" in self.driver.current_url or "checkcaptcha" in self.driver.current_url:
                        print("Обнаружена капча!")
                        time.sleep(20)
                    
                    page_html = self.driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')

                    _number = "none"
                    links = soup.select('._b0ke8 ._2lcm958')

                    for link in links:
                        href = link.get('href', '')
                        number = re.search(r'tel:([+]?[\d\-\s\(\)]{8,})', href)
                        if number:
                            clean_phone = re.sub(r'[^\d+]', '', number.group(1))
                            _number = clean_phone#clean_phone_to_format(clean_phone)

                    page_html = self.driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')
                    
                    
                    containers = self.driver.find_elements(By.CSS_SELECTOR, 'div._z3fqkm')
                    if containers:
                        if len(containers) > 1: 
                            container = containers[1]
                            actions = ActionChains(self.driver)
                            actions.move_to_element(container).click().perform()
                        page_html = self.driver.page_source
                        soup = BeautifulSoup(page_html, 'html.parser')
                        times = soup.select('._dxfma7')
                        if len(times) > 2:
                            times_days = times[0].select('._bt4zwr')
                            _times = ""
                            for _time in times_days:
                                _times += _time.get_text(' ', strip=True) if _time and hasattr(_time, 'get_text') else "" 
                                _times += "\n"
                            _times.rstrip("\n")
                        else:
                            times = soup.select_one('._ksc2xc')
                            _times = times.get_text(' ', strip=True) if times and hasattr(times, 'get_text') else "" 
                            _times = _times.split('  ')[0]

                    restaurant.number = _number
                    restaurant.times = _times

                    org_url = f"https://2gis.ru/tyumen/search/%E2%80%8B{restaurant.address}"
                    self.driver.get(org_url)

                    containers = self.driver.find_elements(By.CSS_SELECTOR, 'div._zjunba')
                    if len(containers) > 0: 
                        container = containers[0]
                        actions = ActionChains(self.driver)
                        actions.move_to_element(container).click().perform()
                    
                    
                    current_url = self.driver.current_url.split('/')
                    while(len(current_url)<9):
                        time.sleep(0.1)
                        current_url = self.driver.current_url.split('/')
                    
                    restaurant.coord = current_url[8].replace('%2C', '|')
                    restaurant.coord = f"{restaurant.coord.split('|')[1]}|{restaurant.coord.split('|')[0]}"
                    print(restaurant.coord)
                    
                    restaurants_to_update.append(restaurant)
                    updated_count += 1
                    
                    print(f"Обновлено: {restaurant.title}")

                    if updated_count%10==0 and restaurants_to_update:
                        self.db.save_to_file(db_file)
                        print(f"Обновлено ресторанов: {updated_count}")
                    else:
                        print("Нет ресторанов для обновления")
                    
                except Exception as e:
                    print(f"Ошибка при парсинге {restaurant.title}: {e}")
                    continue
                
            return updated_count
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def parse_site_add2(self, db_file=None):
        if db_file is None:
            db_file = self.db_file
        
        try:
            print("Загрузка данных из JSON...")
            self.db.load_from_file(db_file)
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            restaurants_to_update = []
            updated_count = 0
            
            for restaurant in self.db.data:
                if restaurant.number != "none" and restaurant.photo_path != "":
                    continue
                    
                print(f"Парсим дополнительную информацию для: {restaurant.title}")
                
                org_url = f"https://2gis.ru/tyumen/firm/{restaurant.urlid}/"
                
                try:
                    response = session.get(org_url, timeout=10)
                    
                    if response.status_code != 200:
                        print(f"Ошибка HTTP {response.status_code} для {restaurant.title}")
                        continue
                    
                    if "captcha" in response.url or "checkcaptcha" in response.url:
                        print("Обнаружена капча! Пропускаем...")
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')

                    _number = "none"
                    phone_links = soup.select('a[href^="tel:"]')
                    
                    for link in phone_links:
                        href = link.get('href', '')
                        number = re.search(r'tel:([+]?[\d\-\s\(\)]{8,})', href)
                        if number:
                            clean_phone = re.sub(r'[^\d+]', '', number.group(1))
                            _number = clean_phone
                            break

                    _times = ""
                
                    time_selectors = [
                        '._dxfma7',
                        '._ksc2xc',
                        '[data-qa="contacts-schedule"]',
                        '.schedule'
                    ]
                    
                    for selector in time_selectors:
                        time_elements = soup.select(selector)
                        if time_elements:
                            for time_elem in time_elements:
                                _times += time_elem.get_text(' ', strip=True) + "\n"
                            break
                    
                    _times = _times.rstrip("\n")
                    
                    restaurant.number = _number
                    restaurant.times = _times
                    
                    restaurants_to_update.append(restaurant)
                    updated_count += 1
                    
                    print(f"Обновлено: {restaurant.title}")
                    
                    time.sleep(0.5)
                    
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
    _url = "https://2gis.ru/tyumen/search/"
    try:
        for i in range(1):
            break
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9A%D0%BE%D1%84%D0%B5%D0%B9%D0%BD%D0%B8/rubricId/162",
                _type = 'Кофейня'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%BA%D0%B0%D0%BB%D1%8C%D1%8F%D0%BD%D0%BD%D1%8B%D0%B5/rubricId/110357",
                _type = 'Кальян'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%91%D0%B0%D1%80%D1%8B",
                _type = 'Бар'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/filters/rubric_id%3D164",
                _type = 'Ресторан'
            );
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/filters/rubric_id%3D161",
                _type = 'Кафе'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/filters/rubric_id%3D165",
                _type = 'Фастфуд'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/filters/rubric_id%3D166",
                _type = 'Столовая'
            )
            results = parser.parse_site(
                url="https://2gis.ru/tyumen/search/%D0%9F%D0%BE%D0%B5%D1%81%D1%82%D1%8C/filters/rubric_id%3D51459",
                _type = 'Пиццерия'
            )
            
        
        start_time = time.time()
        parser.parse_site_add()
        end_time = time.time()
        print(end_time - start_time)

    finally:
        parser.close()
        input("Enter для выхода...")
