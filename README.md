# Geospatial File Measurement API

## Problem Statement overview
This project is a backend service built with FastAPI that accepts geospatial files (Shapefile ZIPs and KMLs), processes the spatial features within them, and dynamically calculates geographic measurements (Area for Polygons, Length for LineStrings) by intelligently transforming coordinate reference systems (CRS) to accurate projected metric planes.

---

## Setup & Installation

### Option 1: Docker (Recommended)
Geospatial libraries (`fiona`, `geopandas`, `shapely`) rely on C-extensions (GEOS/GDAL) which can be notoriously difficult to configure natively across different operating systems. Docker isolates these dependencies seamlessly.

1. Ensure Docker Desktop is running.
2. In the project root, run:
   ```bash
   docker-compose up --build
   ```
3. The API will be available at `http://localhost:8000`.

### Option 2: Local Python Environment
If you have GDAL and GEOS binaries already configured on your system (e.g., via `conda` or Linux package managers):

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install the pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## API Documentation

Interactive Swagger documentation is automatically generated and accessible at **[http://localhost:8000/docs](http://localhost:8000/docs)** while the server is running.

### 1. Upload Geospatial File
**Endpoint**: `POST /api/files/`
- **Description**: Uploads a `.kml` file or a `.zip` archive containing an ESRI Shapefile, parses all internal layers/features, and calculates metric measurements.
- **Request**: `multipart/form-data` with a key `file`.
- **Response** (HTTP 201):
  ```json
  {
      "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
      "filename": "survey_boundary.zip",
      "feature_count": 14,
      "crs": "EPSG:4326",
      "status": "COMPLETED"
  }
  ```

### 2. Retrieve File Information
**Endpoint**: `GET /api/files/{id}/`
- **Description**: Fetches the high-level metadata of a previously processed file.
- **Response** (HTTP 200):
  ```json
  {
      "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
      "filename": "survey_boundary.zip",
      "feature_count": 14,
      "crs": "EPSG:4326",
      "status": "COMPLETED"
  }
  ```

### 3. Retrieve Measurements & Geometries
**Endpoint**: `GET /api/files/{id}/measurements/`
- **Description**: Returns deep extraction details for all features, including their WKT geometry, properties, and dynamically calculated metric measurements.
- **Response** (HTTP 200):
  ```json
  {
    "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
    "filename": "survey_boundary.zip",
    "original_crs": "EPSG:4326",
    "projected_crs": "EPSG:32618 (UTM Zone 18N)",
    "feature_count": 1,
    "features": [
      {
        "feature_id": 1,
        "geometry_type": "Polygon",
        "geometry_wkt": "POLYGON ((-73.98 40.76, -73.95 40.80, -73.94 40.79, -73.98 40.76))",
        "properties": {
          "Name": "Central Park"
        },
        "measurements": {
          "area_sq_meters": 3421103.25,
          "area_hectares": 342.11,
          "perimeter_meters": 9886.42
        },
        "supported": true,
        "message": null
      }
    ]
  }
  ```

---

## Architecture

- **Application Structure**: 
  - Designed with scalability in mind using a modular layout. 
  - `app/api/` contains the routing controllers.
  - `app/services/` holds the core business logic uncoupled from the HTTP transport layer.
  - `app/core/` houses configuration and the complex CRS projection engine.
  - `tests/` features automated `pytest` suites covering ingestion logic and mathematical bounds.
- **File-Processing Flow**: 
  - Uploads are temporarily written to disk. `.zip` files are securely extracted and scanned for `.shp`, `.shx`, and `.dbf` components. `.kml` files are parsed recursively across all internal KML layers/folders. 
  - GeoPandas reads the layers into dataframes, standardizing empty attributes (NaN -> None) for stable JSON serialization.
- **Measurement Calculation Flow**: 
  - Each Shapely geometry object is categorized. 
  - Polygons yield Area and Perimeter. LineStrings yield Length. Points are flagged as supported but skipped for measurement, and GeometryCollections (or unsupported types) are gracefully skipped with a `supported: false` flag to prevent API crashing.
- **CRS Handling**: 
  - Geographic CRS (like standard EPSG:4326 WGS84 coordinates) are mathematically flawed for 2D metric measurements (producing skewed 'degrees squared'). 
  - Our engine calculates the exact global centroid of the incoming geometry and dynamically builds a `pyproj.Transformer` to reproject the geometry to its specific **Universal Transverse Mercator (UTM)** zone (e.g., Zone 18N for New York) before evaluating `.area` and `.length` in metric meters.

---

## Design Decisions & Trade-offs

- **Framework**: I chose **FastAPI** over Django because it provides native asynchronous execution (superior for heavy I/O operations like reading large Shapefiles) and automatically self-documents Pydantic models into interactive Swagger UI, saving hours of manual doc writing.
- **State Storage**: I opted for a thread-safe, in-memory dictionary store (`memory_store.py`) to reduce configuration complexity for the reviewer. In a true production rollout, this would be abstracted to a PostgreSQL database with PostGIS extensions.
- **NumPy Strict Pinning**: I explicitly pinned `numpy<2.0.0` inside `requirements.txt`. NumPy 2.x recently released breaking ABI changes that crash Shapely 2.0.x binary wheels with `ufunc` errors during geometry operations.

---

## Learning and Future Scope

### What I Learned
- Working on this deepened my understanding of how Fiona wraps the GDAL C++ API, specifically discovering that KML files are ingested as isolated "layers" (folders) that must be manually iterated over, unlike flat Shapefiles.
- Implementing dynamic UTM zone logic from scratch taught me how to securely bounce coordinates back and forth between a geometry's native CRS, WGS84 for zone calculation, and the final metric projection.

### Future Scope
1. **Background Task Queuing**: For enterprise drone survey orthomosaics, shapefiles and GeoTIFFs can easily exceed gigabytes. Integrating Celery + Redis would allow the endpoint to return a `202 ACCEPTED` status immediately while the file is processed on a background worker.
2. **PostGIS Integration**: Storing the WKT geometries in a spatial database to allow querying for features via bounding box intersections (e.g., "return all extracted polygons inside California").
3. **Multi-Format Support**: Expanding support for modern Cloud Optimized GeoTIFFs (COG) and GeoPackage (`.gpkg`) which offer significantly faster I/O than traditional ESRI Shapefiles.
