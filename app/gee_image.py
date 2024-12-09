# app/gee_image.py

import ee, geemap, numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from app.subpolygon import SubPolygon
import json

class GeeImage:
    
    def __init__(self) -> None:
        self.roi = []
        self.bands = []
        self.img_array = []
        self.normalized_image = []
        self.satellite_image = None
        self.start_date = '2023-01-01'
        self.end_date = '2024-03-31'
        self.scale = 30
        self.roi_array = []

    def setRoiData(self, data):
        geojson = data.get('geojson', None)
        if not geojson:
            with open('./json_files/india_roi.json', 'r') as file:
                roi_json = json.load(file)
                self.roi = roi_json['india_roi']
        else:
          self.roi = data['geojson'][0]['geometry']['coordinates'][0] 
          polygon_array = SubPolygon(self.roi)
          self.roi_array = polygon_array.getSubPolygons()
        self.bands = [band for band in data['bands'].values()]
        if data.get('date', None):
            self.end_date = data['date']
            date_obj = datetime.strptime(self.start_date, '%Y-%m-%d')
            new_date = date_obj - relativedelta(years=1)
            self.start_date = new_date.strftime('%Y-%m-%d')

    
    def getImage(self, coord):
        roi = ee.Geometry.Polygon([coord])

        def mask_s2_clouds(image):
            cloud_prob_mask = image.select('MSK_CLDPRB').lt(50)  # Cloud probability threshold (less than 50%)
            cirrus_mask = image.select('MSK_CLASSI_CIRRUS').eq(0)  # No cirrus clouds
            mask = cloud_prob_mask.And(cirrus_mask)
            return image.updateMask(mask).divide(10000)

        # Fetch Sentinel-2 image collection
        sentinal_collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(self.start_date, self.end_date)
            .filterBounds(roi)
            .map(mask_s2_clouds)
        )

        sentinal_image = sentinal_collection.median().select(self.bands)
        sentinal_band = sentinal_image.select(self.bands[0])
        crs = sentinal_band.projection().crs().getInfo()
        sentinal_image = sentinal_image.reproject(crs=crs, scale=self.scale).clip(roi)

        # Clip the resulting image to the ROI
        image_clipped = sentinal_image.clip(roi)
        image_clipped = image_clipped.updateMask(image_clipped.clip(roi).mask())
        sentinal_bounds = image_clipped.geometry().bounds().getInfo()
        img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        normalized_image = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))
        geoJson = self.toGeojson(coord)
        self.img_array.append((img_array, sentinal_bounds['coordinates'][0]))
        return (img_array, sentinal_bounds['coordinates'][0])


    def getImageUrl(self):
        roi = ee.Geometry.Polygon(self.roi)

        # Fetch Sentinel-2 image collection
        sentinal_collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(self.start_date, self.end_date) \
            .filterBounds(roi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        )

        sentinal_image = sentinal_collection.median().clip(roi)

        vis_params = {
            "bands": self.bands,  # RGB bands
            "min": 0,
            "max": 3000,
            'gamma': 0.9
        }

        # Generate tile URL for dynamic scaling
        map_id_dict = sentinal_image.getMapId(vis_params)
        url = map_id_dict["tile_fetcher"].url_format
        return url


    def getBands(self):
        return self.bands

    def getRawImage(self):
        return self.img_array
    
    def getNormalizedImage(self):
        return self.normalized_image
    
    
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




