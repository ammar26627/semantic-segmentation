import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from app.process_image import preprocess, get_area

class ImageThread:
    def __init__(self, helper, queue):
        self.helper = helper
        self.area = defaultdict(list)
        

    def worker(self, coord, i):
        # Call the image processing function
        image = self.helper(coord)
        image_png = preprocess(image[0], False)  # Your preprocessing function
        base_64 = base64.b64encode(image_png.getvalue()).decode('utf-8')  # Convert to base64
        
        self.queue.put({
            "status": "Loading",
            "coordinates": self.toGeojson(coord),
            "image": base_64
        })

    

    def image_with_thread_pool(self, num_threads, items, isMask=False):
        # Use a ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.worker, item, i) for i, item in enumerate(items)]
            for future in as_completed(futures):
                future.result()  # Wait for each task to complete
        if isMask:
            self.queue.put({
                "status": "Done",
                "area": self.area
            })
        else:
            self.queue.put({
                "status": "Completed",
            })

    def mask_worker(self, img_array, i):
        mask = Models(img_array, self.helper)
        mask_pngs = mask.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            self.area[key] += get_area(mask_png, mask.scale)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        
        self.queue.put({
            "status": "Loading",
            "id": i,
            "masks": masks_base_64
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
