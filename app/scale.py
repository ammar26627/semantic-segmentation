import math

class Scale:
    def __init__(self, area):
        self.area = area  # Area in m²
        self.max_bytes = 50_000_000  # Maximum bytes GEE allows
        self.bytes_per_pixel = 12  # Assuming 16-bit depth with 3 bands
        
    def calculate_scale_and_satellite(self):
        # Maximum number of pixels GEE allows
        max_pixels = self.max_bytes / self.bytes_per_pixel
        
        # Calculate scale
        scale = math.sqrt(self.area / max_pixels)
        print(scale, self.area, (self.area)/(20*20))
        # Define scales and corresponding satellites
        scale_list = [20]  # Scales in meters
        satellite_list = [
            'COPERNICUS/S2_SR_HARMONIZED',  # Sentinel-2
            # 'LANDSAT/LC09/C02/T1_L2',       # Landsat
        ]
        
        # Assign the best matching scale and satellite
        for i, sc in enumerate(scale_list):
            if scale <= sc:
                self.scale = sc
                self.satellite = satellite_list[i]
                break
        else:
            # Default to the largest scale and satellite
            self.scale = scale_list[-1]
            self.satellite = satellite_list[-1]
        
        return self.scale, self.satellite