import ee, geemap, numpy as np

class GeeImage():
    '''
    Improvements
    1) Set filter date dynamically
    2) Set Scale dynamically
    '''
    def __init__(self) -> None:
        self.roi = []
        self.bands = []
        self.scale = 30
        self.img_array = []
        self.normalized_image = []
        self.sentinal_image = None

    def setRoiData(self, data):
        self.roi = data['geojson'][0][0]['geometry']['coordinates'][0]
        self.bands = [ band for band in data['bands'].values()]
        self.scale = 30
    
    def getImage(self):
        roi = ee.Geometry.Polygon([self.roi])
        self.sentinel_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate('2023-01-01', '2023-01-31') \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first() \
        .select(self.bands)
        image_clipped = self.sentinel_image.clip(roi)
        self.img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=10)
        self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))

    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image
    
    @classmethod
    def initialize_earth_engine(cls):
        try:
            ee.Initialize()
        except ee.EEException:
            ee.Authenticate()
            ee.Initialize()
