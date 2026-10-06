import os
from tests.fixtures.sample_test_files import generate_sample_kml, generate_sample_shapefile_zip

def test_upload_kml_polygon_and_linestring_point(client, tmp_path):
    kml_path = os.path.join(tmp_path, "test.kml")
    generate_sample_kml(kml_path)
    
    with open(kml_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.kml", f, "application/vnd.google-earth.kml+xml")})
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] == 3
    
    file_id = data["id"]
    
    info_response = client.get(f"/api/files/{file_id}/")
    assert info_response.status_code == 200
    assert info_response.json()["id"] == file_id
    
    meas_response = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_response.status_code == 200
    meas_data = meas_response.json()
    assert len(meas_data["features"]) == 3
    
    features = meas_data["features"]
    
    poly_feat = next(f for f in features if f["geometry_type"] == "Polygon")
    assert poly_feat["measurements"]["area_sq_meters"] > 0
    assert poly_feat["supported"] is True
    
    line_feat = next(f for f in features if f["geometry_type"] == "LineString")
    assert line_feat["measurements"]["length_meters"] > 0
    assert line_feat["supported"] is True
    
    pt_feat = next(f for f in features if f["geometry_type"] == "Point")
    assert pt_feat["measurements"] is None
    assert pt_feat["supported"] is True
    assert "Point geometry" in pt_feat["message"]


def test_upload_shapefile_zip(client, tmp_path):
    zip_path = os.path.join(tmp_path, "test.zip")
    generate_sample_shapefile_zip(zip_path)
    
    with open(zip_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.zip", f, "application/zip")})
        
    assert response.status_code == 201
    assert response.json()["feature_count"] == 1


def test_invalid_file_extension(client, tmp_path):
    txt_path = os.path.join(tmp_path, "test.txt")
    with open(txt_path, "w") as f:
        f.write("test")
        
    with open(txt_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("test.txt", f, "text/plain")})
        
    assert response.status_code == 400
    assert "error" in response.json()


def test_corrupted_shapefile_zip(client, tmp_path):
    import zipfile
    zip_path = os.path.join(tmp_path, "corrupt.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("test.shp", "dummy content")
        
    with open(zip_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("corrupt.zip", f, "application/zip")})
        
    assert response.status_code == 400
    assert "Missing .shx file" in response.json()["error"]


def test_get_file_info_and_measurements_404(client):
    response = client.get("/api/files/nonexistent-id/")
    assert response.status_code == 404
    
    response = client.get("/api/files/nonexistent-id/measurements/")
    assert response.status_code == 404


def test_unsupported_geometry_graceful_handling(client, tmp_path):
    import geopandas as gpd
    from shapely.geometry import GeometryCollection
    import zipfile
    
    shp_path = os.path.join(tmp_path, "unsup_test.shp")
    gc = GeometryCollection([])
    gdf = gpd.GeoDataFrame({'name': ['Test GC'], 'geometry': [gc]}, crs="EPSG:4326")
    gdf.to_file(shp_path)
    
    zip_path = os.path.join(tmp_path, "unsup_test.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            fpath = shp_path.replace('.shp', ext)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=f"unsup_test{ext}")
                
    with open(zip_path, "rb") as f:
        response = client.post("/api/files/", files={"file": ("unsup_test.zip", f, "application/zip")})
        
    assert response.status_code == 201
    file_id = response.json()["id"]
    
    meas_response = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_response.status_code == 200
    feat = meas_response.json()["features"][0]
    assert feat["supported"] is False
    assert feat["measurements"] is None
