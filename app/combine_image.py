import numpy as np
from shapely.geometry import Polygon
from pyproj import Transformer
import matplotlib.pyplot as plt


def merge_images_with_geojson(images_with_geojson, resolution=10):
    """
    Merge multiple images using their GeoJSON geometries.

    Args:
        images_with_geojson: List of tuples, where each tuple contains:
            - `image_array`: The image as a NumPy array (H, W, C), normalized or uint8.
            - `geojson`: GeoJSON object containing the geographical bounds.
        resolution: Resolution of the output image in meters per pixel.

    Returns:
        combined_image: Merged image as a NumPy array.
    """
    if not images_with_geojson:
        raise ValueError("Input list is empty")
    
    transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    
    # Step 1: Calculate UTM bounds for each image and determine overall bounds
    utm_polygons = []
    for image_array, geojson in images_with_geojson:
        try:
            # Parse coordinates from the given GeoJSON format
            if geojson['type'] != 'Polygon' or 'coordinates' not in geojson:
                raise ValueError("Invalid GeoJSON format. Must contain 'type': 'Polygon' and 'coordinates'.")
            
            polygon_coords = geojson['coordinates'][0]  # Use the first ring
            geo_shape = Polygon(polygon_coords)
            
            # Transform GeoJSON coordinates to UTM
            utm_coords = [transformer_to_utm.transform(*coord) for coord in geo_shape.exterior.coords]
            utm_polygon = Polygon(utm_coords)
            utm_polygons.append((utm_polygon, image_array))
        except Exception as e:
            print(f"Error processing GeoJSON: {e}")
    
    # Determine overall bounds
    minx = min(poly.bounds[0] for poly, _ in utm_polygons)
    miny = min(poly.bounds[1] for poly, _ in utm_polygons)
    maxx = max(poly.bounds[2] for poly, _ in utm_polygons)
    maxy = max(poly.bounds[3] for poly, _ in utm_polygons)
    
    # Step 2: Initialize canvas
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    combined_image = np.zeros((height, width, 3), dtype=np.float32)
    
    # Step 3: Place images on the canvas
    for utm_polygon, image_array in utm_polygons:
        bounds = utm_polygon.bounds
        x_off = int((bounds[0] - minx) / resolution)
        y_off = int((maxy - bounds[3]) / resolution)
        
        h, w, c = image_array.shape
        
        # Ensure alignment with the canvas
        canvas_h, canvas_w, _ = combined_image.shape
        slice_h = min(h, canvas_h - y_off)
        slice_w = min(w, canvas_w - x_off)
        
        if slice_h > 0 and slice_w > 0:
            trimmed_image = image_array[:slice_h, :slice_w, :]
            canvas_slice = combined_image[y_off:y_off + slice_h, x_off:x_off + slice_w, :]
            
            # Merge image using averaging for overlapping areas
            np.add(canvas_slice, trimmed_image, out=canvas_slice, where=(canvas_slice == 0))
    
    # Normalize values to range [0, 255] if needed
    # combined_image = np.clip(combined_image * 255, 0, 255).astype(np.uint8)
    
    return combined_image