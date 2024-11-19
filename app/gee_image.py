# app/gee_image.py

import ee, geemap, numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from app.satellite_image import SatelliteImage
from app.scale import Scale
from pyproj import Geod
import math

class GeeImage():

    def __init__(self) -> None:
        self.roi = []
        self.bands = []
        self.scale = 30 # Set to dynamic
        self.img_array = []
        self.normalized_image = []
        self.satellite_image = None
        self.start_date = '2024-01-01'
        self.end_date = '2024-03-31'
        self.area = 0
        self.satellite = None
        self.scale = None
        self.satellite = None
        self.MAX_PIXELS = 12_582_912

    def setRoiData(self, data):
        self.roi = data['geojson'][0]['geometry']['coordinates'][0]
        self.bands = [band for band in data['bands'].values()]
        # self.scale = data['scale']
        # if data.get('date', None):
        #     self.start_date = data['date']
        #     date_obj = datetime.strptime(self.start_date, '%Y-%m-%d')
        #     new_date = date_obj + relativedelta(months=1)
        #     self.end_date = new_date.strftime('%Y-%m-%d')

    
    def getImage(self):
        roi = ee.Geometry.Polygon([self.roi])
        self.area = roi.area().getInfo()

        self.satellite_image = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .mean()

        image_clipped = self.satellite_image.clip(roi)
        self.img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))


    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image