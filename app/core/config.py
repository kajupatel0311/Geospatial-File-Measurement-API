import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Geospatial File Measurement API"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/geospatial_uploads" if os.name != "nt" else "C:\\tmp\\geospatial_uploads")
    ALLOWED_EXTENSIONS: set = {".zip", ".kml"}
    MAX_FILE_SIZE: int = 50 * 1024 * 1024

    def __init__(self):
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

settings = Settings()
