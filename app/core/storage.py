from pathlib import Path
from uuid import uuid4

from app.config import settings


class LocalStorage:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or settings.UPLOAD_STORAGE_DIR)

    def save_bytes(self, data: bytes, filename: str, folder: str = "uploads") -> dict:
        target_dir = self.root / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name
        storage_name = f"{uuid4().hex}_{safe_name}"
        path = target_dir / storage_name
        path.write_bytes(data)
        return {
            "storage_key": str(path.relative_to(self.root)).replace("\\", "/"),
            "file_name": safe_name,
            "size": len(data),
        }

    def read_bytes(self, storage_key: str) -> bytes:
        path = (self.root / storage_key).resolve()
        root = self.root.resolve()
        if root not in path.parents and path != root:
            raise ValueError("storage key resolves outside storage root")
        return path.read_bytes()


storage = LocalStorage()
