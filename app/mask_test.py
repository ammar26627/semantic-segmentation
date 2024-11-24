# from __init__ import initialize_earth_engine
import ee, geemap, numpy as np
from PIL import Image
import json, os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

def initialize_earth_engine():
    load_dotenv()
    data = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    credentials = json.loads(data)
    scopes = ['https://www.googleapis.com/auth/earthengine']
    credentials = Credentials.from_service_account_info(credentials, scopes= scopes)
    ee.Initialize(credentials)

initialize_earth_engine()
roi = ee.Geometry.Polygon([ [
            [
              77.68115228391895,
              29.494415139920207
            ],
            [
              77.68115228391895,
              29.448616818035887
            ],
            [
              77.72791268238785,
              29.448616818035887
            ],
            [
              77.72791268238785,
              29.494415139920207
            ],
            [
              77.68115228391895,
              29.494415139920207
            ]
          ]])
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
crs = "EPSG:4326"  # Explicitly set the CRS to WGS84
worldcover_rgb = worldcover.visualize(**vis_params).reproject(crs, None, 30)
mask_array = geemap.ee_to_numpy(worldcover_rgb, region=roi, scale=30)
normalized_mask = (mask_array - np.min(mask_array)) / (np.max(mask_array) - np.min(mask_array))
# print(max(mask_array[0]))
image_array = (normalized_mask * 255).astype(np.uint8)
image = Image.fromarray(image_array)
image.save('normalized_mask.png')
