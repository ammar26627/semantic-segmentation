import ee, numpy as np
from gee_image import GeeImage
from collections import defaultdict
class ImageMask(GeeImage):
    def __init__(self) -> None:
        super().__init__()
        self.features = {}
        self.features_geometries = defaultdict(list)
        self.color_map = {None: [0, 0, 0], 0: [0, 0, 0]}
        self.model = ""
        self.feature_image = None
        self.pixels = defaultdict(list)
        self.mean = defaultdict(list)
        self.cov = defaultdict(list)
        self.threshold = None

    def setClassData(self, data):
        for i, element in enumerate(data['geojson'], 1):
            self.features_geometries[element['properties']['class']].append(element['geometry']['coordinates'][0])
            self.features[element['properties']['class']] = i
            self.color_map[i] = self.hexToRgb(element['properties']['fill'])
        self.model = data['model']
        self.threshold = data['threshold']

    def mask(self):
        ee_geometry = defaultdict[list]
        for key, value in self.features_geometries.items():
            ee_geometry[key].append(ee.Geometry.Polygon([value]))

        all_geometries = []
        for value in ee_geometry.values():
            all_geometries += value

        combine_ee_geometry = all_geometries[0]
        for element in all_geometries[1:]:
            combine_ee_geometry = combine_ee_geometry.union(element)
        self.feature_image = self.sentinel_image.clip(combine_ee_geometry)

        for key in self.features:
            for element in self.features_geometries[key]:
                self.pixels[key].append(self.sample_region(element))
            self.pixels[key] = np.vstack(self.pixels[key])
            self.means[key] = np.mean(self.pixels[key], axis=0)
            self.cov[key] = np.cov(self.pixels[key],  rowvar=False)

    

    def sample_region(self, region):
        sampled = self.feature_image.sample(region=region, scale=self.scale, numPixels=500)
        pixels = sampled.select(self.bands).getInfo()
        values = [x['properties'] for x in pixels['features']]
        return np.array([[x[b] for b in self.bands] for x in values])
    
    @classmethod
    def hexToRgb(cls, hex):
        hex = hex.lstrip('#')
        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        return [r, g, b]

        