# app/gee_image.py

import ee, geemap, numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from app.satellite_image import SubPolygon
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
        self.mask_array = []
        self.normalized_mask = []
        self.satellite_image = None
        self.start_date = '2020-04-01'
        self.end_date = '2022-01-31'
        self.area = 0
        self.satellite = None
        self.scale = 30
        self.satellite = None
        self.MAX_PIXELS = 12_582_912
        self.roi_array = []
        
        
        """ORIGINAL ROI"""

    def setRoiData(self, data):
        self.roi = data['geojson'][0]['geometry']['coordinates'][0]
        polygon_array = SubPolygon(self.roi)
        self.roi_array = polygon_array.getSubPolygons()
        self.bands = [band for band in data['bands'].values()]
        
        # self.scale = data['scale']
        # if data.get('date', None):
        #     self.start_date = data['date']
        #     date_obj = datetime.strptime(self.start_date, '%Y-%m-%d')
        #     new_date = date_obj + relativedelta(months=1)
        #     self.end_date = new_date.strftime('%Y-%m-%d')
        
        
        """ORIGINAL ROI END"""
        
        
    #     """MRADUL ROI"""
        
    # def setRoiData(self, data):
    #     geometry = data["geojson"][0]["geometry"]
    #     type_ = geometry["type"]
    #     match type_:
    #         case "Polygon":
    #             coordinates = [geometry["coordinates"]]
    #         case "MultiPolygon":
    #             coordinates = geometry["coordinates"]
    #         case _:
    #             print("Invalid geometry type")
    #     for coordinate in coordinates:
    #         roi = coordinate[0]
    #         polygon_array = SubPolygon(roi)
    #         self.roi.extend(roi)
    #         self.roi_array.extend(polygon_array.getSubPolygons())
    #     self.bands = [band for band in data["bands"].values()]
        
    #     """MRADUL ROI END"""
        

    
    def getImage(self, coord):
        roi = ee.Geometry.Polygon([coord])

        def maskS2clouds(image):
            """Mask clouds and cloud shadows in Sentinel-2 images"""
            # Get QA60 band - bit 10 is clouds, bit 11 is cirrus
            qa = image.select('QA60')
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            
            # Create cloud-free mask
            mask = qa.bitwiseAnd(cloudBitMask).eq(0) \
                .And(qa.bitwiseAnd(cirrusBitMask).eq(0))

            # Apply scaling factors
            scaled = image.divide(10000) \
                .select(['B.*']) \
                .multiply(10000) \
                .updateMask(mask) \
                .copyProperties(image, ['system:time_start'])

            return scaled

        dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date)
        
        # s2_col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        #     .filterBounds(roi) \
        #     .filterDate(self.start_date, self.end_date) \
        #     .map(lambda image: image.updateMask(image.select('QA60').eq(0))) \
        #     .sort('CLOUDY_PIXEL_PERCENTAGE') \

        satellite_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .mean()
        
        sentinal_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
            .mean()

                

                
        linked_col = dw_col.linkCollection(satellite_image, satellite_image.bandNames())

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
        # top1_prob_hillshade = ee.Terrain.hillshade(top1_prob.multiply(100)).divide(255)

        # Combine RGB visualization with the hillshade effect
        # dw_rgb_hillshade = dw_rgb.multiply(top1_prob)

        # self.satellite_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        #     .filterBounds(roi) \
        #     .filterDate(self.start_date, self.end_date) \
        #     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        #     .mean()
        
        image_clipped = sentinal_image.clip(roi)
        img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=30)
        normalized_image = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))
        # self.img_array.append(img_array)
        # self.normalized_image.append(normalized_image)

        mask_array = geemap.ee_to_numpy(dw_rgb, region=roi, scale=30)
        mask_array = np.flipud(mask_array)  # Correct orientation if rotated
        normalized_mask = (mask_array - np.min(mask_array)) / (np.max(mask_array) - np.min(mask_array))
        # self.mask_array.append(mask_array)
        # self.normalized_mask.append(normalized_mask)
        return (normalized_mask, normalized_image)
        # roi = ee.Geometry.Polygon([self.roi])
        # self.area = roi.area().getInfo()

        # self.satellite_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        #     .filterBounds(roi) \
        #     .filterDate(self.start_date, self.end_date) \
        #     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        #     .mean()

        # image_clipped = self.satellite_image.clip(roi)
        # self.img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        # self.normalized_image = (self.img_array - np.min(self.img_array)) / (np.max(self.img_array) - np.min(self.img_array))


    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image
    
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
    




