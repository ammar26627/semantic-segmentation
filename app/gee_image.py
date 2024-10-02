# app/gee_image.py

import ee, geemap, numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime

class GeeImage():

    def __init__(self) -> None:
        self.roi = []
        self.bands = []
        self.scale = 30
        self.img_array = []
        self.normalized_image = []
        self.sentinal_image = None
        self.start_date = '2023-03-01'
        self.end_date = '2023-03-31'

    def setRoiData(self, data):
        self.roi = data['geojson'][0]['geometry']['coordinates'][0]
        self.bands = [ band for band in data['bands'].values()]
        self.scale = 30
        if data.get('date', None):
            self.start_date = data['date']
            date_obj = datetime.strptime(self.start_date, '%Y-%m-%d')
            new_date = date_obj + relativedelta(months=1)
            self.end_date = new_date.strftime('%Y-%m-%d')

    
    def getImage(self):
        roi = ee.Geometry.Polygon([self.roi])
        self.sentinal_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(self.start_date, self.end_date) \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first() \
        .select(self.bands)
        image_clipped = self.sentinal_image.clip(roi)
        self.img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))

    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image

