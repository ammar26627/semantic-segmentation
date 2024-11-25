import json
from shapely.geometry import Polygon, MultiPolygon, mapping, LineString
from shapely.ops import split
from pyproj import Transformer, Geod

class SubPolygon:
    def __init__(self, coordinates):
        self.max_area = 150_000_000
        transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
        utm_coords = [transformer_to_utm.transform(lon, lat) for lon, lat in coordinates]
        polygon = Polygon(utm_coords)
        self.polygon = polygon

    def subdivide_irregular_polygon(self):
        sub_polygons = []
        stack = [self.polygon]
        while stack:
            poly = stack.pop()
            area = poly.area
            if area <= self.max_area:
                sub_polygons.append(poly)
            else:
                # Split using a horizontal or vertical line
                minx, miny, maxx, maxy = poly.bounds
                if (maxx - minx) > (maxy - miny):
                    # Split vertically
                    split_line = LineString([(poly.centroid.x, miny), (poly.centroid.x, maxy)])
                else:
                    # Split horizontally
                    split_line = LineString([(minx, poly.centroid.y), (maxx, poly.centroid.y)])
                # Try splitting and handle GeometryCollection
                try:
                    divided = split(poly, split_line)
                    for geom in divided.geoms:
                        if isinstance(geom, Polygon):
                            stack.append(geom)
                except Exception as e:
                    print(f"Skipping problematic geometry: {e}")
        return sub_polygons
    
    def getSubPolygons(self):
        transformer_to_latlon = Transformer.from_crs("EPSG:32644", "EPSG:4326", always_xy=True)
        subdivided_polygons = self.subdivide_irregular_polygon()
        sub_polygon_array = []
        for i, sub_polygon in enumerate(subdivided_polygons):
            # Transform UTM coordinates back to lat/lon
            latlon_coords = [transformer_to_latlon.transform(x, y) for x, y in sub_polygon.exterior.coords]
            sub_polygon_array.append(latlon_coords)
        return sub_polygon_array