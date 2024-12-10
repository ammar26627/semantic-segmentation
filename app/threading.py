# app/threading.py

import base64, numpy as np, cv2
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
        print(image)
        mask = Models(image, self.object)
        mask_pngs = mask.getColoredMask()
        masks_base_64 = {}
        for key, mask_png in mask_pngs.items():
            # classgeojson = prashant(mask_png)
            self.area[key] += get_area(mask_png, 30)
            png = preprocess(mask_png, True)
            masks_base_64[key] = base64.b64encode(png.getvalue()).decode('utf-8')
        print(masks_base_64)
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
    
    @staticmethod
    def generate_geojson_from_dict(image_dict, corners, geojson_data, color_map, epsilon_factor=0.001, contour_area_threshold=10):

        height, width, _ = next(iter(image_dict.values())).shape  # Assuming all images have the same shape
        top_left, top_right, bottom_right, bottom_left = corners

        # Functions for coordinate transformations
        def pixel_to_geo(pixel):
            return (
                float(top_left[0] + (pixel[0] / width) * (top_right[0] - top_left[0])),
                float(top_left[1] + (pixel[1] / height) * (bottom_left[1] - top_left[1]))
            )

        # Process each class and its corresponding image
        for class_name, image in image_dict.items():
            # Get the class color from the predefined color map (normalized RGB to 0-255)
            class_color = color_map.get(class_name)
            if class_color is None:
                print(f"Error: No color mapping found for class '{class_name}'. Skipping.")
                continue
            # Convert normalized color to 0-255 range
            class_color = tuple(int(c * 255) for c in class_color)

            # Convert normalized image to 0-255 range
            image = (image * 255).astype(np.uint8)

            # Convert image to a binary mask based on class color
            mask = cv2.inRange(image, class_color, class_color)
            binary_mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1]

            # Find contours for the current class in the image
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) < contour_area_threshold:
                    continue

                # Simplify the contour
                epsilon = epsilon_factor * cv2.arcLength(contour, True)
                polygon = cv2.approxPolyDP(contour, epsilon, True)

                # Convert pixel coordinates to geographic coordinates
                coordinates = [pixel_to_geo(tuple(pt[0])) for pt in polygon]

                # Ensure the polygon is closed
                if coordinates and coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])

                # Create a GeoJSON feature for the current class
                feature = {
                    'type': 'Feature',
                    'properties': {'class': class_name},
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [coordinates]
                    }
                }
                geojson_data['features'].append(feature)

        return geojson_data
