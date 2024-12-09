# app/threading.py

import base64, numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.process_image import preprocess, get_area
from collections import defaultdict
from app.models import Models

class ImageThread:
    def __init__(self, img_object, object, queue):
        self.img_object = img_object
        self.object = object
        self.area = defaultdict(float)
        self.queue = queue
        self.geojson = {}
        for key in object.features.keys():
            self.geojson[key] = self.toGeojson(key)
        

    def image_ml_worker(self, coord, i):
        image = self.img_object.getImage(coord)
        self.ml(image[0], image[1])

    def ml_worker(self, image, i):
        self.ml(image[0], image[1])
    
    def ml(self, image, coord):
        mask = Models(image, self.object)
        mask_pngs = mask.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            # classgeojson = prashant(mask_png)
            self.area[key] += get_area(mask_png, 30)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        self.queue.put({
            "status": "Loading...",
            "top_left": self.get_top_left_coordinate(coord[:-1]),
            "shape": image.shape,
            "masks": masks_base_64
        })


    def dl_worker(self, coord, i):
        image = self.img_object.getImage(coord)
        dl = self.object
        dl.unet(image[0])
        mask_pngs = dl.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            self.area[key] += get_area(mask_png, 30)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        self.queue.put({
            "status": "Loading...",
            "top_left": self.get_top_left_coordinate(image[1][:-1]),
            "shape": image.shape,
            "masks": masks_base_64
        })


    def thread_pool(self, num_threads, items, function):
        match function:
            case 'ml':
                worker = self.ml_worker

            case 'image_ml':
                worker = self.image_ml_worker

            case "dl":
                worker = self.dl_worker

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, item, i) for i, item in enumerate(items)]
            for future in as_completed(futures):
                future.result()
        self.queue.put({
            "status": "Completed",
            "area": self.area
        })

    
    @staticmethod
    def get_top_left_coordinate(coords):
        top_left = None
        for coord in coords:
            lon, lat = coord
            if top_left is None or lat > top_left[1] or (lat == top_left[1] and lon < top_left[0]):
                top_left = coord      
        return top_left
    
    @staticmethod
    def toGeojson(feature_class):
        geoJson = {
            'type': 'FeatureCollection',
            'features': [
                {
                'type': 'Feature',
                'properties': {'class': feature_class},
                'geometry': {
                    'coordinates': [
                    ],
                    'type': 'Polygon'
                }
                }
            ]
        }
        return geoJson
