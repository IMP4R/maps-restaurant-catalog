import { PlaceService } from '../models/place';
import * as fs from 'fs';
import * as path from 'path';

interface JsonPlace {
    id: string;
    title: string;
    address: string;
    photo_url: string;
    photo_path: string;
    coord: string;
    raiting: string;
    type: string;
    category: string;
    number: string;
    times: string;
}

async function importPlaces() {
    try {
        const jsonPath = path.join(__dirname, '../../places.json');
        const jsonData = fs.readFileSync(jsonPath, 'utf8');
        const places: JsonPlace[] = JSON.parse(jsonData);

        console.log(`Найдено ${places.length} заведений`);

        let successCount = 0;
        let errorCount = 0;

        for (const placeData of places) {
            try {
                const place = {
                    id: placeData.id,
                    title: placeData.title,
                    address: placeData.address,
                    photo_url: placeData.photo_url,
                    photo_path: placeData.photo_path,
                    coord: placeData.coord,
                    raiting: placeData.raiting,
                    type: placeData.type,
                    category: placeData.category,
                    number: placeData.number,
                    times: placeData.times.split(' ​ ')[0]
                };

                await PlaceService.addPlace(place);
                successCount++;
                console.log(`Добавлено: ${place.title}`);
                
            } catch (error) {
                errorCount++;
                console.log(`Ошибка с: ${placeData.title}`, error);
            }
        }

        console.log(`\nИмпорт завершен!`);
        console.log(`Успешно: ${successCount}`);
        console.log(`Ошибок: ${errorCount}`);

    } catch (error) {
        console.error('Ошибка импорта:', error);
    }
}

importPlaces();