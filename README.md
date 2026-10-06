# Geospatial File Measurement API

A FastAPI-based backend service for uploading, processing, and analyzing geospatial files. The API supports **KML files** and **Shapefile ZIP archives**, extracts their spatial features and attributes, and calculates accurate **area, perimeter, and length measurements** using CRS-aware geospatial transformations.

## Problem Statement

Geospatial data is commonly stored in coordinate systems such as **WGS84 (EPSG:4326)**, where coordinates are represented in degrees. Directly calculating distances or areas using geographic coordinates can produce inaccurate results.

This project provides a REST API that:

- Accepts `.kml` files and `.zip` archives containing Shapefiles.
- Extracts geospatial features, geometries, CRS, and attributes.
- Calculates:
  - **Area and perimeter** for Polygon geometries.
  - **Length** for LineString geometries.
  - No measurement for Point geometries.
- Automatically transforms geographic coordinates into an appropriate projected **UTM CRS** before performing metric calculations.
- Handles unsupported geometries gracefully without crashing the API.

---

## Technology Stack

- **Python**
- **FastAPI**
- **GeoPandas**
- **Shapely**
- **PyProj**
- **Fiona / GDAL**
- **Pydantic**
- **Pytest**
- **Docker**

---

## Setup & Installation

### Option 1: Docker — Recommended

Geospatial libraries such as Fiona, GeoPandas, and Shapely depend on native libraries including GDAL and GEOS. Docker provides a consistent environment across operating systems.

Make sure Docker Desktop is installed and running.

From the project root:

```bash
docker-compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

### Option 2: Local Python Environment

If GDAL and GEOS dependencies are already available on your system:

#### 1. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On Linux/macOS:

```bash
source venv/bin/activate
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

#### 3. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

# API Documentation

## 1. Upload Geospatial File

### `POST /api/files/`

Uploads and processes a KML file or a ZIP archive containing an ESRI Shapefile.

The API extracts the available features and calculates the appropriate measurements.

### Request

`multipart/form-data`

Parameter:

```text
file
```

Supported formats:

```text
.kml
.zip
```

### Example Response

```json
{
  "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
  "filename": "survey_boundary.zip",
  "feature_count": 14,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

---

## 2. Retrieve File Information

### `GET /api/files/{id}/`

Returns high-level metadata for a previously processed file.

### Example Response

```json
{
  "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
  "filename": "survey_boundary.zip",
  "feature_count": 14,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

---

## 3. Retrieve Measurements

### `GET /api/files/{id}/measurements/`

Returns detailed information about all extracted features, including:

- Feature ID
- Geometry type
- Geometry in WKT format
- Properties/attributes
- Original CRS
- Projected CRS
- Calculated measurements
- Support status
- Processing messages

### Example Response

```json
{
  "id": "7878d655-b4c2-466d-862d-a4176cfce41b",
  "filename": "survey_boundary.zip",
  "original_crs": "EPSG:4326",
  "projected_crs": "EPSG:32618",
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

# Architecture

The project follows a modular service-oriented structure:

```text
geospatial-measurement-api/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │
│   ├── core/
│   │   └── ...
│   │
│   ├── services/
│   │   └── ...
│   │
│   ├── main.py
│   └── ...
│
├── tests/
│   └── ...
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Application Structure

- `app/api/` — API routes and request handling.
- `app/services/` — Core file-processing and measurement logic.
- `app/core/` — Configuration and CRS transformation logic.
- `tests/` — Automated tests for file processing and measurement calculations.

This separation keeps HTTP handling independent from the core geospatial processing logic.

---

# File Processing Flow

The processing pipeline follows these steps:

```text
File Upload
     │
     ▼
File Validation
     │
     ├── KML
     │
     └── Shapefile ZIP
             │
             ▼
       Temporary Extraction
             │
             ▼
       GeoPandas / Fiona
             │
             ▼
      Feature Extraction
             │
             ▼
       CRS Detection
             │
             ▼
    CRS Transformation
             │
             ▼
    Measurement Calculation
             │
             ▼
       JSON API Response
```

For Shapefile ZIP archives, the system validates and extracts the required Shapefile components such as:

```text
.shp
.shx
.dbf
```

KML files are parsed through their available layers/features.

Empty attribute values are normalized where necessary to ensure reliable JSON serialization.

---

# Measurement Calculation

Each extracted geometry is classified according to its geometry type.

| Geometry | Measurement |
|---|---|
| Polygon | Area + Perimeter |
| MultiPolygon | Area + Perimeter |
| LineString | Length |
| MultiLineString | Length |
| Point | No measurement |
| Unsupported geometry | Gracefully skipped |

Unsupported geometries do not cause the entire API request to fail. Instead, the response provides an appropriate `supported` status and message.

---

# CRS Handling

Accurate geospatial measurements require calculations in a projected coordinate system with metric units.

For example:

```text
EPSG:4326
Latitude / Longitude
Degrees
```

should not be directly used for:

```text
Area
Distance
Perimeter
```

The API therefore follows a CRS-aware workflow:

```text
Input Geometry
      │
      ▼
Original CRS
      │
      ▼
Transform to WGS84 if required
      │
      ▼
Determine appropriate UTM Zone
      │
      ▼
Transform geometry to UTM
      │
      ▼
Calculate measurements in meters
```

For geographic coordinates, the system dynamically determines an appropriate **UTM zone based on the geometry's location** and transforms the geometry before calculating area, perimeter, or length.

This prevents calculations from being performed directly in geographic degrees.

---

# Design Decisions & Trade-offs

## FastAPI

FastAPI was selected because it provides:

- Simple REST API development.
- Automatic OpenAPI documentation.
- Interactive Swagger UI.
- Pydantic-based request validation.
- Clear separation between API and business logic.
- Good support for building high-performance Python APIs.

The computationally intensive geospatial operations are handled through GeoPandas, Shapely, Fiona/GDAL, and PyProj.

## In-Memory Storage

The current implementation uses an in-memory store for processed file metadata and results.

This keeps the project lightweight and avoids unnecessary database configuration for the assignment.

For a production deployment, the storage layer could be replaced with:

```text
PostgreSQL + PostGIS
```

without significantly changing the API layer.

## Dependency Compatibility

The project pins compatible versions of geospatial dependencies to reduce issues caused by binary compatibility between packages such as:

```text
NumPy
Shapely
GDAL
Fiona
GeoPandas
```

---

# Testing

The project includes automated tests using **Pytest**.

Tests cover areas such as:

- File upload validation.
- KML processing.
- Shapefile processing.
- Geometry extraction.
- Polygon area calculation.
- LineString length calculation.
- Point handling.
- CRS transformation.
- Unsupported geometry handling.
- API response validation.

Run the tests using:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

---

# Example Use Cases

The API can be used for applications such as:

- Land and property measurement.
- Survey data processing.
- GIS data analysis.
- Route and distance calculation.
- Mapping applications.
- Infrastructure planning.
- Agricultural land analysis.
- Drone and geographic survey workflows.

---

# Learning Outcomes

This project provided practical experience with:

- Building REST APIs using FastAPI.
- Processing real-world geospatial data.
- Working with GeoPandas, Shapely, Fiona, and PyProj.
- Understanding geographic vs. projected coordinate systems.
- Implementing dynamic UTM zone selection.
- Performing accurate spatial measurements.
- Designing modular backend services.
- Writing automated tests for geospatial applications.
- Containerizing applications with Docker.

---

# Future Scope

### 1. Background Processing

Large geospatial datasets can require significant processing time.

A production implementation could use:

```text
Celery + Redis
```

to process large files asynchronously and return:

```text
202 ACCEPTED
```

while the processing job runs in the background.

### 2. PostGIS Integration

A PostgreSQL/PostGIS database could be introduced to:

- Store geometries.
- Query spatial relationships.
- Perform bounding-box searches.
- Find intersecting features.
- Support spatial indexing.

### 3. Additional File Formats

Future versions could support:

- GeoPackage (`.gpkg`)
- GeoJSON
- GeoTIFF
- Cloud Optimized GeoTIFF (COG)
- Other common GIS formats.

### 4. Authentication & Rate Limiting

For production deployment, the API could be extended with:

- JWT/API-key authentication.
- Rate limiting.
- File-size limits.
- User-level access control.
- Request logging and monitoring.

---

# Conclusion

The **Geospatial File Measurement API** provides a modular and CRS-aware backend solution for processing geospatial files and calculating reliable spatial measurements.

The project focuses on correctness, clean API design, graceful error handling, and maintainable architecture while keeping the implementation lightweight enough for easy local development and evaluation.

https://github.com/kajupatel0311/Geospatial-File-Measurement-API
