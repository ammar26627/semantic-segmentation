import numpy as np
from shapely.geometry import box
from pyproj import Transformer
from rasterio.transform import from_bounds
from rasterio.features import rasterize

def merge_masks(sub_polygon_coords, masks, resolution=10):
    """
    Merge subdivided masks into a single large image.

    Parameters:
        sub_polygon_coords (list): List of subdivided polygon coordinates in lat/lon.
        masks (dict): Dictionary where keys are indices of polygons and values are corresponding mask arrays.
        resolution (float): Resolution of the final image in the same units as the coordinates.

    Returns:
        np.ndarray: Merged mask as a single image.
    """
    # Transform polygons to UTM (or a suitable projected CRS for pixel alignment)
    transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    utm_polygons = []
    for coords in sub_polygon_coords:
        utm_coords = [transformer_to_utm.transform(lon, lat) for lon, lat in coords]
        utm_polygons.append(box(*np.array(utm_coords).reshape(-1, 2).T.flatten()))
    
    # Determine the overall bounding box
    overall_bounds = np.array([poly.bounds for poly in utm_polygons])
    minx, miny, maxx, maxy = overall_bounds[:, 0].min(), overall_bounds[:, 1].min(), overall_bounds[:, 2].max(), overall_bounds[:, 3].max()
    
    # Calculate final image dimensions
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)

    # Initialize the combined image
    combined_image = np.zeros((height, width), dtype=np.uint8)

    # Transform each mask into its corresponding position
    for i, polygon in enumerate(utm_polygons):
        mask = masks[i]
        bounds = polygon.bounds
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], mask.shape[1], mask.shape[0])
        
        # Rasterize and merge
        rasterized = rasterize([(polygon, 1)], out_shape=mask.shape, transform=transform)
        x_off = int((bounds[0] - minx) / resolution)
        y_off = int((maxy - bounds[3]) / resolution)
        combined_image[y_off:y_off + mask.shape[0], x_off:x_off + mask.shape[1]] += mask * rasterized

    return combined_image
