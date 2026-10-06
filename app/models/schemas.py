from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class MeasurementData(BaseModel):
    area_sq_meters: Optional[float] = None
    area_hectares: Optional[float] = None
    perimeter_meters: Optional[float] = None
    length_meters: Optional[float] = None
    length_km: Optional[float] = None

class FeatureMeasurement(BaseModel):
    feature_id: int
    geometry_type: str
    geometry_wkt: str
    properties: Dict[str, Any]
    measurements: Optional[MeasurementData] = None
    supported: bool
    message: Optional[str] = None

class FileMetadata(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str
    status: str

class FileMeasurementsResponse(BaseModel):
    id: str
    filename: str
    original_crs: str
    projected_crs: str
    feature_count: int
    features: List[FeatureMeasurement]

class ErrorResponse(BaseModel):
    error: str
