import numpy as np
from shapely.geometry import Polygon
from pyproj import Transformer
import matplotlib.pyplot as plt

def merge_images_with_geojson_and_roi(images_with_geojson, combined_roi, resolution=10):
    """
    Merge multiple images using their GeoJSON geometries and a combined ROI.

    Args:
        images_with_geojson: List of tuples, where each tuple contains:
            - `image_array`: The image as a NumPy array (H, W, C), normalized or uint8.
            - `geojson`: GeoJSON object containing the geographical bounds.
        combined_roi: GeoJSON defining the overall bounds for the merged image.
        resolution: Resolution of the output image in meters per pixel.

    Returns:
        combined_image: Merged image as a NumPy array.
    """
    if not images_with_geojson:
        raise ValueError("Input list is empty")
    
    transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    
    # Parse combined ROI to UTM
    if combined_roi['type'] != 'Polygon' or 'coordinates' not in combined_roi:
        raise ValueError("Invalid combined ROI format. Must contain 'type': 'Polygon' and 'coordinates'.")
    roi_coords = combined_roi['coordinates'][0]
    roi_polygon = Polygon(roi_coords)
    utm_coords = [transformer_to_utm.transform(*coord) for coord in roi_polygon.exterior.coords]
    utm_roi_polygon = Polygon(utm_coords)
    roi_bounds = utm_roi_polygon.bounds

    # Determine overall canvas size
    minx, miny, maxx, maxy = roi_bounds
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    combined_image = np.zeros((height, width, 3), dtype=np.float32)
    
    # Step 2: Process and place each image
    for image_array, geojson in images_with_geojson:
        try:
            image_array = np.flipud(image_array)  # Flip image vertically
            
            # Parse image bounds from GeoJSON
            polygon_coords = geojson['coordinates'][0]
            geo_shape = Polygon(polygon_coords)
            utm_coords = [transformer_to_utm.transform(*coord) for coord in geo_shape.exterior.coords]
            utm_polygon = Polygon(utm_coords)
            bounds = utm_polygon.bounds

            # Calculate offsets relative to combined ROI
            x_off = int((bounds[0] - minx) / resolution)
            y_off = int((maxy - bounds[3]) / resolution)

            # Determine slice dimensions
            h, w, c = image_array.shape
            slice_h = min(h, height - y_off)
            slice_w = min(w, width - x_off)

            if slice_h > 0 and slice_w > 0:
                # Trim the image to fit the canvas bounds
                trimmed_image = image_array[:slice_h, :slice_w, :]
                canvas_slice = combined_image[y_off:y_off + slice_h, x_off:x_off + slice_w, :]

                # Merge image using averaging for overlapping areas
                np.add(canvas_slice, trimmed_image, out=canvas_slice, where=(canvas_slice == 0))
        except Exception as e:
            print(f"Error processing image: {e}")

    # Normalize values to range [0, 255] if needed
    combined_image = np.clip(combined_image * 255, 0, 255).astype(np.uint8)
    
    return combined_image
