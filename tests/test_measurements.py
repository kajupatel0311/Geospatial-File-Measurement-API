from shapely.geometry import Polygon
from app.core.crs import get_utm_epsg
from app.services.measurement_service import calculate_measurements

def test_crs_projection_accuracy():
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    meas = calculate_measurements(poly, "EPSG:4326")
    area_sq_meters = meas["measurements"]["area_sq_meters"]
    assert 1.0e10 < area_sq_meters < 1.3e10
    
def test_utm_epsg():
    epsg = get_utm_epsg(72.8, 19.0)
    assert epsg == 32643
