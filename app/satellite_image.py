import ee

class SatelliteImage:
    def __init__(self, roi, satellite, start_date, end_date, bands):
        self.roi = roi
        self.start_date = start_date
        self.end_date = end_date
        self.extended_start_date = '2021-12-01'
        self.bands = bands
        self.primary_dataset = None
        self.secondary_dataset = None
        self.satellite = satellite
        self.set_layers()

        if self.satellite == 'LANDSAT/LC09/C02/T1_L2':
            self.satellite_image = self.landsat_image()
        elif self.satellite == 'COPERNICUS/S2_SR_HARMONIZED':
            self.satellite_image = self.sentinal_image()
 
    
    def set_layers(self):
        self.primary_dataset = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.start_date, self.end_date)

        # self.secondary_dataset = ee.ImageCollection(self.satellite) \
        #     .filterBounds(self.roi) \
        #     .filterDate(self.extended_start_date, self.end_date)
        
    def sentinal_image(self):
        sentinal_primary = self.primary_dataset.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).mean()
        return sentinal_primary
    
    def landsat_image(self):
        landsat_primary = self.primary_dataset.filter(ee.Filter.lt('CLOUD_COVER', 20)).mean()
        return landsat_primary
    