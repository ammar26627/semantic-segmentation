import ee

class SatelliteImage:
    def __init__(self, roi, satellite, start_date, end_date, bands):
        """
        Initialize the composite class with ROI, date range, and bands.
        """
        self.roi = roi
        self.start_date = start_date
        self.end_date = end_date
        self.extended_start_date = '2022-12-01'
        self.bands = bands
        self.primary_dataset = None
        self.secondary_dataset = None
        self.satellite = satellite
        self.set_layers()
        self.satellite_image = self.sentinal_image()

    @staticmethod
    def mask_clouds(image):
        # """
        # Masks clouds and cloud shadows based on the QA_PIXEL band.
        # """
        # qa_pixel = image.select('QA_PIXEL')
        # cloud_bit_mask = (1 << 4)  # Bit 4 indicates clouds
        # cloud_shadow_bit_mask = (1 << 3)  # Bit 3 indicates cloud shadows
        # mask = qa_pixel.bitwiseAnd(cloud_bit_mask).eq(0) \
        #                .And(qa_pixel.bitwiseAnd(cloud_shadow_bit_mask).eq(0))
        # return image.updateMask(mask)
        pass
    
    @staticmethod
    def sentinal_mask_cloud(image):
        """
        Masks clouds and cloud shadows based on the QA10, QA20, and QA60 bands.
        """
        # Select the QA bands
        qa10 = image.select('QA10')
        qa20 = image.select('QA20')
        qa60 = image.select('QA60')
        
        # Define cloud and cloud shadow bitmask for each QA band
        cloud_bit_mask = (1 << 4)  # Bit 4 indicates clouds (QA10)
        cloud_shadow_bit_mask = (1 << 3)  # Bit 3 indicates cloud shadows (QA20)
        
        # Create masks for cloud and cloud shadow using the QA bands
        cloud_mask = qa10.bitwiseAnd(cloud_bit_mask).eq(0)
        cloud_shadow_mask = qa20.bitwiseAnd(cloud_shadow_bit_mask).eq(0)
        
        # Combine the masks for cloud and cloud shadows and apply it to the image
        mask = cloud_mask.And(cloud_shadow_mask).And(qa60.eq(0))  # QA60 is for atmospheric conditions
        
        # Update the mask and return the image
        return image.updateMask(mask)


    @staticmethod
    def apply_scale_factors(image):
        """
        Applies scaling factors to optical and thermal bands.
        """
        optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
        return image.addBands(optical_bands, None, True) \
                    .addBands(thermal_bands, None, True)
    
    def set_layers(self):
        self.primary_dataset = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.start_date, self.end_date) \
            .map(self.sentinal_mask_cloud)

        # Secondary dataset (extended date range)
        self.secondary_dataset = ee.ImageCollection(self.satellite) \
            .filterBounds(self.roi) \
            .filterDate(self.extended_start_date, self.end_date) \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first() \
        
    def sentinal_image(self):
        sentinal_primary = self.primary_dataset.map(self.sentinal_mask_cloud)
        sentinal_secondary = self.secondary_dataset.map(self.sentinal_mask_cloud)
        combined_dataset = sentinal_primary.merge(sentinal_secondary)
        composite = combined_dataset.median()
        return composite.clip(self.roi).select(self.bands)
    
    # def landsat_image(self):
    #     landsat_primary = self.primary_dataset.map(self.mask_clouds).map(self.apply_scale_factors)
    #     landsat_secondary = self.secondary_dataset.map(self.mask_clouds).map(self.apply_scale_factors)
    #     combined_dataset = landsat_primary.merge(landsat_secondary)
    #     composite = combined_dataset.median()
    #     return composite.clip(self.roi).select(['SR_'+band for band in self.bands])


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
    