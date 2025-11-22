import json
from pathlib import Path
from typing import Any


class DatabaseManager:
    """
    Singleton для управления JSON-хранилищем данных
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            from ..infra.settings import settings
            cls._instance.data_dir = Path(settings.get("data_dir", "data"))
            cls._instance.data_dir.mkdir(exist_ok=True)
        return cls._instance
    
    def _get_file_path(self, collection: str) -> Path:
        """возвращает путь к файлу коллекции"""
        return self.data_dir / f"{collection}.json"
    
    def load_collection(self, collection: str, default: Any = None) -> Any:
        """загружает данные из коллекции"""
        file_path = self._get_file_path(collection)
        
        if not file_path.exists():
            return default if default is not None else []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default if default is not None else []
    
    def save_collection(self, collection: str, data: Any):
        """сохраняет данные в коллекцию"""
        file_path = self._get_file_path(collection)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


db = DatabaseManager()