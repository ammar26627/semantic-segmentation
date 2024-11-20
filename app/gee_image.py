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
        dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date)

        # Load Sentinel-2 Image Collection and apply cloud masking
        s2_col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date) \
            .map(lambda image: image.updateMask(image.select('QA60').eq(0)))  # Mask clouds using QA60 band

        # Link Dynamic World and Sentinel-2 Collections (alignment)
        linked_col = dw_col.linkCollection(s2_col, s2_col.first().bandNames())

        # Get the first linked image (Dynamic World and Sentinel-2)
        linked_img = ee.Image(linked_col.first())

        # Visualization palette for Dynamic World land cover classes
        vis_palette = [
            '419bdf', '397d49', '88b053', '7a87c6', 'e49635', 'dfc35a',
            'c4281b', 'a59b8f', 'b39fe1'
        ]

        # Create RGB visualization from the 'label' band (land cover classification)
        dw_rgb = linked_img.select('label').visualize(min=0, max=8, palette=vis_palette)

        # Get the most likely class probability
        class_names = [
            'water', 'trees', 'grass', 'flooded_vegetation', 'crops',
            'shrub_and_scrub', 'built', 'bare', 'snow_and_ice'
        ]

        top1_prob = linked_img.select(class_names).reduce(ee.Reducer.max())

        # Create a hillshade effect for the most likely class probability
        top1_prob_hillshade = ee.Terrain.hillshade(top1_prob.multiply(100)).divide(255)

        # Combine RGB visualization with the hillshade effect
        dw_rgb_hillshade = dw_rgb.multiply(top1_prob_hillshade)

        self.img_array = geemap.ee_to_numpy(dw_rgb_hillshade, region=roi, scale=10)
        self.img_array = np.flipud(self.img_array)  # Correct orientation if rotated
        self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))


    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image