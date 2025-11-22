from abc import ABC, abstractmethod
from typing import Dict

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """базовый класс для валют"""
    
    def __init__(self, name: str, code: str):
        self._validate_code(code)
        self._validate_name(name)
        
        self._name = name
        self._code = code.upper()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def code(self) -> str:
        return self._code
    
    @abstractmethod
    def get_display_info(self) -> str:
        """строковое представление для интерфейса/логов"""
        pass
    
    def _validate_code(self, code: str):
        """валидация кода валюты"""
        if not isinstance(code, str):
            raise ValueError("Currency code must be a string")
        if not (2 <= len(code) <= 5):
            raise ValueError("Currency code must contain 2-5 characters")
        if not code.isalpha():
            raise ValueError("Currency code must contain only letters")
        if not code.isupper():
            raise ValueError("Currency code must be in uppercase")
    
    def _validate_name(self, name: str):
        """валидация названия валюты"""
        if not isinstance(name, str):
            raise ValueError("Currency name must be a string")
        if not name.strip():
            raise ValueError("Currency name cannot be empty")


class FiatCurrency(Currency):
    """фиатная валюта"""
    
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self._issuing_country = issuing_country
    
    @property
    def issuing_country(self) -> str:
        return self._issuing_country
    
    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """крипта"""
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = market_cap
    
    @property
    def algorithm(self) -> str:
        return self._algorithm
    
    @property
    def market_cap(self) -> float:
        return self._market_cap
    
    def get_display_info(self) -> str:
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap > 0 else "N/A"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


"""реестр валют"""
_CURRENCY_REGISTRY: Dict[str, Currency] = {}

def register_currency(currency: Currency):
    """регистрирует валюту в реестре"""
    _CURRENCY_REGISTRY[currency.code] = currency

def get_currency(code: str) -> Currency:
    """возвращает валюту по коду"""
    code = code.upper()
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return _CURRENCY_REGISTRY[code]

def get_all_currencies() -> Dict[str, Currency]:
    """возвращает все зарегистрированные валюты"""
    return _CURRENCY_REGISTRY.copy()


def initialize_currencies():
    """инициализация реестра валют"""
    
    register_currency(FiatCurrency("US Dollar", "USD", "United States"))
    register_currency(FiatCurrency("Euro", "EUR", "Eurozone"))
    register_currency(FiatCurrency("Russian Ruble", "RUB", "Russia"))
    register_currency(FiatCurrency("British Pound", "GBP", "United Kingdom"))
    register_currency(FiatCurrency("Japanese Yen", "JPY", "Japan"))
   
    register_currency(CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12))
    register_currency(CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11))
    register_currency(CryptoCurrency("Litecoin", "LTC", "Scrypt", 5.8e9))
    register_currency(CryptoCurrency("Cardano", "ADA", "Ouroboros", 1.2e10))


initialize_currencies()