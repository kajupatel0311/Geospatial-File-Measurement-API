import os
import zipfile
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
import fiona

def generate_sample_kml(filepath: str):
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    fiona.drvsupport.supported_drivers['libkml'] = 'rw'
    
    p = Polygon([(72.8, 19.0), (72.8, 19.1), (72.9, 19.1), (72.9, 19.0), (72.8, 19.0)])
    l = LineString([(72.8, 19.0), (72.9, 19.1)])
    pt = Point(72.85, 19.05)
    
    gdf = gpd.GeoDataFrame({
        'name': ['Test Poly', 'Test Line', 'Test Point'],
        'geometry': [p, l, pt]
    }, crs="EPSG:4326")
    
    gdf.to_file(filepath, driver='KML')

def generate_sample_shapefile_zip(filepath: str):
    temp_dir = filepath + "_tmp"
    os.makedirs(temp_dir, exist_ok=True)
    shp_path = os.path.join(temp_dir, "test.shp")
    
    p = Polygon([(72.8, 19.0), (72.8, 19.1), (72.9, 19.1), (72.9, 19.0), (72.8, 19.0)])
    gdf = gpd.GeoDataFrame({
        'name': ['Test Poly'],
        'geometry': [p]
    }, crs="EPSG:4326")
    
    gdf.to_file(shp_path)
    
    with zipfile.ZipFile(filepath, 'w') as zf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                zf.write(os.path.join(root, file), arcname=file)
