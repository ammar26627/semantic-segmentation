# app/gee_image.py

import ee, geemap, numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from app.satellite_image import SatelliteImage
from pyproj import Geod
import math

class GeeImage():

    def __init__(self) -> None:
        self.roi = []
        self.bands = ['SR_B4', 'SR_B3', 'SR_B2']
        self.scale = 500 # Set to dynamic
        self.img_array = []
        self.normalized_image = []
        self.satellite_image = None
        self.start_date = '2021-12-01'
        self.end_date = '2024-03-31'
        self.area = 0
        self.satellite = None
        self.scale = 30
        self.satellite = 'COPERNICUS/S2_SR_HARMONIZED'
        self.MAX_PIXELS = 12_582_912

    def setRoiData(self, data):
        self.roi = data['geojson'][0]['geometry']['coordinates'][0]
        # print(self.roi)
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
        self.setScale()
        print(self.roi)
        print(self.area)
        print(self.scale)
        start_date = '2021-12-01'
        end_date = '2024-02-01'
        self.bands = ['B4', 'B3', 'B2']  # True Color bands (Red, Green, Blue)

        # Create Landsat composite
        composite = SatelliteImage(roi, self.satellite, start_date, end_date, self.bands)

        # Get the composite image
        self.satellite_image = composite.satellite_image
        image_clipped = self.satellite_image.clip(roi)
        self.img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))

    def setScale(self):
        # scale = math.sqrt(self.area/self.MAX_PIXELS)
        # scale_list = [30,] #500 30
        # satellite_list = ['LANDSAT/LC09/C02/T1_L2',] #'MODIS/006/MOD09GA'  'COPERNICUS/S2_SR_HARMONIZED', 
        # for i, sc in enumerate(scale_list):
        #     if scale <= sc:
        #         self.scale = sc
        #         self.satellite = satellite_list[i]
        #         break
        # else:
        #     self.scale = scale_list[-1]
        #     self.satellite = satellite_list[-1]
        self.scale = 10

    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image