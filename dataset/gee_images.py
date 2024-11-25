from subpolygons import SubPolygon
import geemap, ee, numpy as np

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

    def setRoiData(self, data):
        geometry = data["geojson"][0]["geometry"]
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
        self.bands = [band for band in data["bands"].values()]
        

    
    def getImage(self, coord):
        roi = ee.Geometry.Polygon([coord])
        sentinal_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
            .mean()
        

        image_clipped = sentinal_image.clip(roi)
        img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=30)
        normalized_image = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))

        worldcover = ee.ImageCollection('ESA/WorldCover/v100').first().clip(roi)
        vis_params = {
            'min': 10,
            'max': 100,
            'palette': [
                '006400',  # Trees (10) - dark green
                'ffbb22',  # Shrubland (20) - orange
                'ffff4c',  # Grassland (30) - yellow
                'f096ff',  # Cropland (40) - pink
                'fa0000',  # Built-up (50) - red
                'b4b4b4',  # Bare/sparse (60) - gray
                '0064c8',  # Snow/ice (70) - blue
                '0096a0',  # Water (80) - cyan
                '00cf75',  # Wetland (90) - light green
                'fae6a0'   # Mangroves (95) - beige
            ]
        }

        worldcover_rgb = worldcover.visualize(**vis_params)
        mask_array = geemap.ee_to_numpy(worldcover_rgb, region=roi, scale=self.scale)
        normalized_mask = (mask_array - np.min(mask_array)) / (np.max(mask_array) - np.min(mask_array))
        return (normalized_mask, normalized_image)
        