from shapely.geometry.base import BaseGeometry
from app.core.crs import reproject_geometry

def calculate_measurements(geom: BaseGeometry, original_crs: str) -> dict:
    """
    Given a geometry and its original CRS, reproject it to UTM and calculate metrics.
    Returns a dict with measurements, supported status, message, and the projected CRS.
    """
    if geom is None or geom.is_empty:
        return {
            "measurements": None,
            "supported": False,
            "message": "Empty or invalid geometry",
            "projected_crs": None
        }

    geom_type = geom.geom_type
    
    if geom_type in ["Point", "MultiPoint"]:
        _, projected_crs = reproject_geometry(geom, original_crs)
        return {
            "measurements": None,
            "supported": True,
            "message": "Point geometry - no measurement required",
            "projected_crs": projected_crs
        }
    
    if geom_type in ["Polygon", "MultiPolygon"]:
        transformed_geom, projected_crs = reproject_geometry(geom, original_crs)
        area = transformed_geom.area
        perimeter = transformed_geom.length
        return {
            "measurements": {
                "area_sq_meters": round(area, 2),
                "area_hectares": round(area / 10000, 2),
                "perimeter_meters": round(perimeter, 2)
            },
            "supported": True,
            "message": None,
            "projected_crs": projected_crs
        }
        
    if geom_type in ["LineString", "MultiLineString"]:
        transformed_geom, projected_crs = reproject_geometry(geom, original_crs)
        length = transformed_geom.length
        return {
            "measurements": {
                "length_meters": round(length, 2),
                "length_km": round(length / 1000, 2)
            },
            "supported": True,
            "message": None,
            "projected_crs": projected_crs
        }
        
    return {
        "measurements": None,
        "supported": False,
        "message": "Geometry type not supported for measurement",
        "projected_crs": None
    }
