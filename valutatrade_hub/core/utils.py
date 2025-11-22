import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict


class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """создает папку для данных, если она не существует"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def load_json(self, filename: str, default: Any = None) -> Any:
        """читает JSON файл и возвращает данные"""
        filepath = self._get_file_path(filename)
        if not os.path.exists(filepath):
            return default if default is not None else []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default if default is not None else []

    def save_json(self, filename: str, data: Any):
        """записывает данные в JSON файл"""
        filepath = self._get_file_path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def get_next_user_id(self) -> int:
        """генерация следующего ID пользователя"""
        users = self.load_json("users.json", [])
        if not users:
            return 1
        return max(user["user_id"] for user in users) + 1


class ExchangeRateService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._default_rates = {}

    def get_rates(self) -> Dict:
        """загрузка котировок из rates.json"""
        rates = self.data_manager.load_json("rates.json")
        if not rates:
            return {"pairs": {}, "last_refresh": None}
        return rates

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """получает обменный курс из актуальных данных"""
        if from_currency == to_currency:
            return 1.0
        
        rates = self.get_rates()
        
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in rates.get("pairs", {}):
            return rates["pairs"][rate_key]["rate"]
        
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in rates.get("pairs", {}):
            return 1.0 / rates["pairs"][reverse_key]["rate"]
        
        if from_currency != "USD" and to_currency != "USD":
            usd_from = self.get_rate(from_currency, "USD")
            usd_to = self.get_rate(to_currency, "USD")
            if usd_from and usd_to:
                return usd_from / usd_to
        
        return None
def is_rates_fresh(self, ttl_seconds: int = 300) -> bool:
        """проверка актуальности курсов"""
        rates = self.get_rates()
        if "last_refresh" not in rates or not rates["last_refresh"]:
            return False
        
        try:
            last_refresh = datetime.fromisoformat(rates["last_refresh"])
            return (datetime.now() - last_refresh) < timedelta(seconds=ttl_seconds)
        except (ValueError, KeyError):
            return False

def update_rates(self, new_rates: Dict):
        """обнолвление курсов"""
        current_rates = self.get_rates()
        current_rates.update(new_rates)
        self.data_manager.save_json("rates.json", current_rates)


def validate_currency_code(currency_code: str) -> bool:
    """проверка валидности кода валюты"""
    return (isinstance(currency_code, str) and 
            len(currency_code) >= 2 and 
            len(currency_code) <= 5 and
            currency_code.isalpha())

def validate_amount(amount: float) -> bool:
    """проверка валидности суммы"""
    return isinstance(amount, (int, float)) and amount > 0