import json
from dataclasses import dataclass
from typing import Set, List
import hashlib

@dataclass
class Restaurant:
    urlid : str
    title: str
    address: str
    photo_url: str
    photo_path: str
    coord: str
    raiting: str
    type: str
    category: str
    number: str
    times: str

    
    @property
    def id(self) -> str:
        data = f"{self.title.strip().lower()}|{self.address.strip().lower()}|{self.type.strip().lower()}"
        return hashlib.md5(data.encode()).hexdigest()

class RestaurantDB:
    def __init__(self):
        self.restaurants: Set[str] = set()
        self.data: List[Restaurant] = [] 
    
    def add_restaurant(self, restaurant: Restaurant) -> bool:
        if restaurant.id not in self.restaurants:
            self.restaurants.add(restaurant.id)
            self.data.append(restaurant)
            return True
        return False
    
    def add_batch(self, restaurants: List[Restaurant]) -> int:
        added_count = 0
        for restaurant in restaurants:
            if self.add_restaurant(restaurant):
                added_count += 1
        return added_count
    
    def save_to_file(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([{'id': r.urlid,
                        'title': r.title, 
                        'address': r.address, 
                        'photo_url': r.photo_url, 
                        'photo_path': r.photo_path, 
                        'coord': r.coord, 
                        'raiting': r.raiting, 
                        'type': r.type,
                        'category': r.category,
                        'number': r.number,
                        'times': r.times,
                        } for r in self.data], f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filename: str):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.restaurants.clear()
                self.data.clear()
                
                for item in data:
                    restaurant = Restaurant(
                        urlid=item.get('id', ''),
                        title=item.get('title', ''), 
                        address=item.get('address', ''),
                        photo_url=item.get('photo_url', ''), 
                        photo_path=item.get('photo_path', ''), 
                        coord=item.get('coord', ''), 
                        raiting=item.get('raiting', ''), 
                        type=item.get('type', ''), 
                        category=item.get('category', ''),
                        number=item.get('number', 'none'),
                        times=item.get('times', 'none'),
                    )
                    self.restaurants.add(restaurant.id)
                    self.data.append(restaurant)
                    
            print(f"Успешно загружено {len(self.data)} ресторанов")
            
        except FileNotFoundError:
            print(f"Файл {filename} не найден")
        except Exception as e:
            print(f"Ошибка при загрузке файла: {e}")
    
    def __len__(self):
        return len(self.data)