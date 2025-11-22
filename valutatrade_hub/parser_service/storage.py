import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class RatesStorage:
    """класс для работы с хранилищем курсов"""
    
    def __init__(self, config):
        self.config = config
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """создает директорию для данных если не существует"""
        Path("data").mkdir(exist_ok=True)
    
    def save_current_rates(self, rates: Dict[str, float], source: str):
        """сохраняет текущие курсы в rates.json"""
        current_data = {
            "pairs": {},
            "last_refresh": datetime.now().isoformat()
        }
        
        for pair, rate in rates.items():
            current_data["pairs"][pair] = {
                "rate": rate,
                "updated_at": datetime.now().isoformat(),
                "source": source
            }
        
        with open(self.config.RATES_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    def save_historical_record(self, from_currency: str, to_currency: str, rate: float, source: str, meta: dict = None):
        """сохраняет историческую запись в exchange_rates.json"""
        record = {
            "id": f"{from_currency}_{to_currency}_{datetime.now().isoformat()}",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "meta": meta or {}
        }
        
        historical_data = self.load_historical_data()
        historical_data.append(record)
        
        with open(self.config.HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, indent=2, ensure_ascii=False)
    
    def load_historical_data(self) -> List[dict]:
        """загружает исторические данные"""
        if not os.path.exists(self.config.HISTORY_FILE_PATH):
            return []
        
        try:
            with open(self.config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def load_current_rates(self) -> dict:
        """загружает текущие курсы"""
        if not os.path.exists(self.config.RATES_FILE_PATH):
            return {"pairs": {}, "last_refresh": None}
        
        try:
            with open(self.config.RATES_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"pairs": {}, "last_refresh": None}