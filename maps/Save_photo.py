import requests
import os
from urllib.parse import unquote

def download_image(url, folder='images'):

    if not os.path.exists(folder):
        os.makedirs(folder)
    
    try:
        parts = url.split('/')
        number = parts[-3]
        filename_hash = parts[-2]
        
        filename = f"{number}_{filename_hash}.jpg"
        filepath = os.path.join(folder, filename)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return filepath
        
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None

if __name__ == "__main__":
    url = "https://avatars.mds.yandex.net/get-altay/6375058/00000000000000000000000000000000/XXXL"
    download_image(url)