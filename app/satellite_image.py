import ee

class SatelliteImage:
    def __init__(self, roi, satellite, start_date, end_date, bands):
        """
        Initialize the composite class with ROI, date range, and bands.
        """
        self.roi = roi
        self.start_date = start_date
        self.end_date = end_date
        self.extended_start_date = '2021-12-01'
        self.bands = bands
        self.primary_dataset = None
        self.secondary_dataset = None
        self.satellite = satellite
        self.set_layers()
        self.satellite_image = self.sentinal_image()
 


    # @staticmethod
    # def apply_scale_factors(image):
    #     optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    #     thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    #     return image.addBands(optical_bands, None, True) \
    #                 .addBands(thermal_bands, None, True)
    
    def set_layers(self):
        self.primary_dataset = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.start_date, self.end_date)

        # Secondary dataset (extended date range)
        self.secondary_dataset = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.extended_start_date, self.end_date)
        
    def sentinal_image(self):
        sentinal_primary = self.primary_dataset.sort('CLOUDY_PIXEL_PERCENTAGE').first()
        sentinal_secondary = self.secondary_dataset.sort('CLOUDY_PIXEL_PERCENTAGE').first()
        return sentinal_primary
    
    def landsat_image(self):
        landsat_primary = self.primary_dataset.filter(ee.Filter.lt('CLOUD_COVER', 100)).sort('CLOUD_COVER').first()
        landsat_secondary = self.secondary_dataset.filter(ee.Filter.lt('CLOUD_COVER', 100)).sort('CLOUD_COVER').first()
        return landsat_primary


    # def create_composite(self):
    #     """
    #     Creates a composite Landsat 9 image by merging primary and secondary datasets.
    #     """
    #     # Primary dataset
    #     primary_dataset = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
    #         .filterBounds(self.roi) \
    #         .filterDate(self.start_date, self.end_date) \
    #         .map(self.mask_clouds) \
    #         .map(self.apply_scale_factors)

    #     # Secondary dataset (extended date range)
    #     secondary_dataset = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
    #         .filterBounds(self.roi) \
    #         .filterDate(self.extended_start_date, self.end_date) \
    #         .map(self.mask_clouds) \
    #         .map(self.apply_scale_factors)

    #     # Merge datasets
    #     combined_dataset = primary_dataset.merge(secondary_dataset)

    #     # Create a composite using the median
    #     composite = combined_dataset.median()

    #     # Clip to ROI and select desired bands
    #     return composite.clip(self.roi).select(self.bands)
    