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
        self.satellite_image = None
        self.start_date = '2024-01-01'
        self.end_date = '2024-03-31'
        self.area = 0
        self.satellite = None
        self.scale = 30
        self.satellite = None
        self.MAX_PIXELS = 12_582_912
        self.roi_array = []

    def getstatesRoi(self, data):
        geometry = data["features"][0]["geometry"]
        type_ = geometry["type"]
        match type_:
            case "Polygon":
                coordinates = [geometry["coordinates"]]
            case "MultiPolygon":
                coordinates = geometry["coordinates"]
            case _:
                print("Invalid geometry type")
        for coordinate in coordinates:
            roi = coordinate[0]
            polygon_array = SubPolygon(roi)
            self.roi.extend(roi)
            self.roi_array.extend(polygon_array.getSubPolygons())
        self.bands = ['B4', 'B3', 'B2']

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

    
    def getImage(self, coord):
        roi = ee.Geometry.Polygon([coord])
        # self.area = roi.area().getInfo()

        def mask_s2_clouds(image):
            qa = image.select('QA60')  # QA60 band for cloud/cirrus
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
            return image.updateMask(mask).divide(10000)

        # Fetch Sentinel-2 image collection
        sentinal_collection = (
            ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(self.start_date, self.end_date)
            .filterBounds(roi)
            .map(mask_s2_clouds)
        )

        sentinal_image = sentinal_collection.median().select(self.bands)
        sentinal_band = sentinal_image.select(self.bands[0])
        crs = sentinal_band.projection().crs().getInfo()
        sentinal_image = sentinal_image.reproject(crs=crs, scale=self.scale).clip(roi)
        
        image_clipped = sentinal_image.clip(roi)
        img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        normalized_image = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))
        geoJson = self.toGeojson(coord)
        self.img_array.append((img_array, geoJson))
        return (normalized_image, geoJson)


    def getImageUrl(self):
        roi = ee.Geometry.Polygon([self.roi])

        def mask_s2_clouds(image):
            qa = image.select('QA60')  # QA60 band for cloud/cirrus
            cloud_bit_mask = 1 << 10
            cirrus_bit_mask = 1 << 11
            mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
            return image.updateMask(mask).divide(10000)

        # Fetch Sentinel-2 image collection
        sentinal_collection = (
            ee.ImageCollection('COPERNICUS/S2_SR')
            .filterDate(self.start_date, self.end_date)
            .filterBounds(roi)
            .map(mask_s2_clouds)
        )

        sentinal_image = sentinal_collection.median().select(self.bands)
        sentinal_band = sentinal_image.select(self.bands[0])
        crs = sentinal_band.projection().crs().getInfo()
        sentinal_image = sentinal_image.reproject(crs=crs, scale=self.scale).clip(roi)

        vis_params = {
            "bands": self.bands,  # RGB bands
            "min": 0,
            "max": 3000,
        }

        # Generate tile URL for dynamic scaling
        map_id_dict = sentinal_image.getMapId(vis_params)
        return map_id_dict["tile_fetcher"].url_format


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
    




