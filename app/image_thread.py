import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from app.process_image import preprocess


class ImageThread:
    def __init__(self, function):
        self.function = function

    def worker(self, coord, i):
        # Call the image processing function
        mask, image = self.function(coord)
        image_png = preprocess(image, False)  # Your preprocessing function
        mask_png = preprocess(mask, False)
        image_png.save(f'./images/image_{i}.png')
        mask_png.save(f'./masks/mask_{i}.png')
        

    

    def image_with_thread_pool(self, num_threads, items):
        # Use a ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.worker, item, i) for i, item in enumerate(items)]
            for future in as_completed(futures):
                future.result()  # Wait for each task to complete

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
