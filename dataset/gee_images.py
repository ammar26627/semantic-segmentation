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
        # self.area = roi.area().getInfo()

        self.satellite_image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(roi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .mean()
        
        image_clipped = self.satellite_image.clip(roi)
        img_array = geemap.ee_to_numpy(image_clipped, region=roi, bands=self.bands, scale=self.scale)
        normalized_image = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array))
        geoJson = self.toGeojson(coord)
        self.img_array.append((img_array, geoJson))
        return (normalized_image, geoJson)