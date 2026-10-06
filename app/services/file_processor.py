import os
import zipfile
import tempfile
import uuid
import geopandas as gpd
import pandas as pd
import fiona

# Enable KML driver for Fiona / GeoPandas
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['libkml'] = 'rw'

from app.core.config import settings
from app.services.measurement_service import calculate_measurements
from app.storage.memory_store import save_file_record

def process_file(file_path: str, original_filename: str) -> dict:
    ext = os.path.splitext(original_filename)[1].lower()
    file_id = str(uuid.uuid4())
    
    if ext == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
            except zipfile.BadZipFile:
                raise ValueError("Corrupted zip archive.")
            
            shp_files = []
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    if file.lower().endswith('.shp'):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                raise ValueError("No .shp file found in the archive.")
            
            shp_path = shp_files[0]
            base_name = os.path.splitext(shp_path)[0]
            
            if not os.path.exists(base_name + '.shx') and not os.path.exists(base_name + '.SHX'):
                raise ValueError("Missing .shx file in the archive.")
            if not os.path.exists(base_name + '.dbf') and not os.path.exists(base_name + '.DBF'):
                raise ValueError("Missing .dbf file in the archive.")
            
            try:
                gdf = gpd.read_file(shp_path)
            except Exception as e:
                raise ValueError(f"Failed to read shapefile: {e}")
                
    elif ext == ".kml":
        try:
            layers = fiona.listlayers(file_path)
            gdfs = []
            for layer in layers:
                try:
                    gdf_layer = gpd.read_file(file_path, driver='KML', layer=layer)
                    if not gdf_layer.empty:
                        gdfs.append(gdf_layer)
                except Exception:
                    pass
            if not gdfs:
                raise ValueError("No valid features found in KML file.")
            gdf = pd.concat(gdfs, ignore_index=True)
        except Exception as e:
            raise ValueError(f"Failed to read KML file: {e}")
    else:
        raise ValueError("Unsupported file format.")
        
    crs = gdf.crs
    crs_name = f"EPSG:{crs.to_epsg()}" if crs and crs.to_epsg() else "EPSG:4326"
    
    features = []
    projected_crs_set = set()
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
            
        properties = {}
        for k, v in row.items():
            if k == 'geometry':
                continue
            if pd.isna(v):
                properties[k] = None
            else:
                properties[k] = v
                
        meas_result = calculate_measurements(geom, crs_name)
        
        if meas_result["projected_crs"]:
            projected_crs_set.add(meas_result["projected_crs"])
            
        feature = {
            "feature_id": idx + 1,
            "geometry_type": geom.geom_type,
            "geometry_wkt": geom.wkt,
            "properties": properties,
            "measurements": meas_result["measurements"],
            "supported": meas_result["supported"],
            "message": meas_result["message"]
        }
        features.append(feature)
        
    overall_projected_crs = list(projected_crs_set)[0] if projected_crs_set else None
    if overall_projected_crs and len(projected_crs_set) > 1:
        overall_projected_crs = f"{overall_projected_crs} (and {len(projected_crs_set)-1} others)"
        
    if overall_projected_crs and overall_projected_crs.startswith("EPSG:"):
        try:
            epsg = int(overall_projected_crs.split(":")[1].split(" ")[0])
            if 32601 <= epsg <= 32660:
                zone = epsg - 32600
                overall_projected_crs = f"EPSG:{epsg} (UTM Zone {zone}N)"
            elif 32701 <= epsg <= 32760:
                zone = epsg - 32700
                overall_projected_crs = f"EPSG:{epsg} (UTM Zone {zone}S)"
        except:
            pass

    record = {
        "id": file_id,
        "filename": original_filename,
        "original_crs": crs_name,
        "projected_crs": overall_projected_crs or crs_name,
        "feature_count": len(features),
        "status": "COMPLETED",
        "features": features
    }
    
    save_file_record(file_id, record)
    
    return record
