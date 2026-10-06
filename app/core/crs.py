from shapely.geometry.base import BaseGeometry
import shapely.ops
from pyproj import Transformer

def get_utm_epsg(lon: float, lat: float) -> int:
    """Calculate the EPSG code for the UTM zone of a given lon/lat."""
    utm_zone = int((lon + 180) / 6) + 1
    if lat >= 0:
        return 32600 + utm_zone
    else:
        return 32700 + utm_zone

def reproject_geometry(geom: BaseGeometry, original_crs_epsg: str = "EPSG:4326") -> tuple[BaseGeometry, str]:
    """
    Reproject a geometry to its appropriate UTM zone for accurate metric measurements.
    Returns the transformed geometry and the target EPSG code string.
    """
    centroid = geom.centroid
    lon, lat = centroid.x, centroid.y
    
    # Simple check if coordinates are in degrees
    is_geographic = (original_crs_epsg.upper() == "EPSG:4326" or (-180 <= lon <= 180 and -90 <= lat <= 90))
    
    if is_geographic:
        epsg_code = get_utm_epsg(lon, lat)
        projected_crs = f"EPSG:{epsg_code}"
    else:
        # If already projected, project centroid to WGS84 to find correct UTM zone
        transformer_to_wgs84 = Transformer.from_crs(original_crs_epsg, "EPSG:4326", always_xy=True)
        lon_wgs84, lat_wgs84 = transformer_to_wgs84.transform(lon, lat)
        epsg_code = get_utm_epsg(lon_wgs84, lat_wgs84)
        projected_crs = f"EPSG:{epsg_code}"

    transformer = Transformer.from_crs(original_crs_epsg, projected_crs, always_xy=True)
    transformed_geom = shapely.ops.transform(transformer.transform, geom)
    
    return transformed_geom, projected_crs
