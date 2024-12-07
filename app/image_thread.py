import base64, numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.process_image import preprocess, get_area
from collections import defaultdict
from app.models import Models

class ImageThread:
    def __init__(self, object, queue):
        self.object = object
        self.area = defaultdict(float)
        self.queue = queue
        

    def image_worker(self, coord, i):
        image = self.object.getImage(coord)
        image_png = preprocess(image[0], False)  # Your preprocessing function
        base_64 = base64.b64encode(image_png.getvalue()).decode('utf-8')  # Convert to base64
        self.queue.put({
            "status": "Loading",
            "center": self.calculateCenter(coord[:-1]),
            "image": base_64
        })

    def ml_worker(self, img_array, i):
        mask = Models(img_array[0], self.object)
        mask_pngs = mask.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            self.area[key] += get_area(mask_png, 30)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        self.queue.put({
            "status": "Loading",
            "coordinates":self.toGeojson(img_array[1]),
            "masks": masks_base_64
        })

    def dl_worker(self, img_array, i):
        dl = self.object
        dl.unet(img_array)
        mask_pngs = dl.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            self.area[key] += get_area(mask_png, 30)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        self.queue.put({
            "status": "Loading",
            "coordinates":self.toGeojson(img_array[1]),
            "masks": masks_base_64
        })


    

    def image_with_thread_pool(self, num_threads, items, function):
        match function:

            case "ml":
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(self.ml_worker, item, i) for i, item in enumerate(items)]
                    for future in as_completed(futures):
                        future.result()
                self.queue.put({
                    "status": "Completed",
                    "area": self.area
                })

            case "dl":
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(self.dl_worker, item, i) for i, item in enumerate(items)]
                    for future in as_completed(futures):
                        future.result()
                self.queue.put({
                    "status": "Completed",
                    "area": self.area
                })

            case "image":
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(self.image_worker, item, i) for i, item in enumerate(items)]
                    for future in as_completed(futures):
                        future.result()  # Wait for each task to complete
                self.queue.put({
                    "status": "Completed",
                })


    @staticmethod
    def toGeojson(coord):
        geoJson = {
            'type': 'FeatureCollection',
            'features': [
                {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'coordinates': [
                        coord
                    ],
                    'type': 'Polygon'
                }
                }
            ]
        }
        return geoJson
    
    @staticmethod
    def calculateCenter(coord):
        import numpy as np
        coordinates = np.array(coord)
        center = np.mean(coordinates, axis=0)
        lat_center = center[0]
        lon_center = center[1]
        return lat_center, lon_center
