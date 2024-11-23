import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from app.process_image import preprocess

class ImageThread:
    def __init__(self, function, sse_queue):
        self.function = function
        self.sse_queue = sse_queue

    def worker(self, coord, i):
        # Call the image processing function
        image = self.function(coord)
        image_png = preprocess(image[0], False, i)  # Your preprocessing function
        base_64 = base64.b64encode(image_png.getvalue()).decode('utf-8')  # Convert to base64
        
        self.sse_queue.put({
            "status": "completed",
            "coordinates": self.toGeojson(coord),
            "image": base_64
        })

    

    def image_with_thread_pool(self, num_threads, items):
        # Use a ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.worker, item, i) for i, item in enumerate(items)]
            for future in as_completed(futures):
                future.result()  # Wait for each task to complete
        self.sse_queue.put("Done")

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
