import json
import os
from typing import Any, Dict, List
from datetime import datetime


class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """создание data/ если отсутствует"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def load_json(self, filename: str, default: Any = None) -> Any:
        """загрузка из json файла"""
        filepath = self._get_file_path(filename)
        if not os.path.exists(filepath):
            return default if default is not None else []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default if default is not None else []

    def save_json(self, filename: str, data: Any):
        """сохраенение в json файл"""
        filepath = self._get_file_path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


class ExchangeRateService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._default_rates = {
            "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
            "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
            "RUB_USD": {"rate": 0.01016, "updated_at": datetime.now().isoformat()},
            "ETH_USD": {"rate": 3720.00, "updated_at": datetime.now().isoformat()},
            "source": "DefaultRates",
            "last_refresh": datetime.now().isoformat()
        }

    def get_rates(self) -> Dict:
        """загрузка котировок"""
        rates = self.data_manager.load_json("rates.json")
        if not rates:
            rates = self._default_rates
            self.data_manager.save_json("rates.json", rates)
        return rates

    def get_rate(self, from_currency: str, to_currency: str):
        
        rates = self.get_rates()
        
        if from_currency == to_currency:
            return 1.0
        
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in rates:
            return rates[rate_key]["rate"]
        
        
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in rates:
            return 1.0 / rates[reverse_key]["rate"]
        
        return None

    def update_rates(self, new_rates: Dict):
        """обновление курсов"""
        current_rates = self.get_rates()
        current_rates.update(new_rates)
        current_rates["last_refresh"] = datetime.now().isoformat()
        self.data_manager.save_json("rates.json", current_rates)