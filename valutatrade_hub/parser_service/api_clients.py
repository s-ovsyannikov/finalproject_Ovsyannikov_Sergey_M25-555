import logging
from abc import ABC, abstractmethod
from typing import Dict

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """абстрактный базовый класс для API клиентов"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.logger = logging.getLogger('parser')
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """получает курсы валют от API"""
        pass
    
    def _make_request(self, url: str) -> dict:
        """выполняет HTTP запрос с обработкой ошибок"""
        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise ApiRequestError(f"Network error: {e}")
        except ValueError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            raise ApiRequestError(f"Invalid response format: {e}")


class CoinGeckoClient(BaseApiClient):
    """клиент для CoinGecko API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """получает курсы криптовалют"""
        self.logger.info("Fetching crypto rates from CoinGecko")
        
        crypto_ids = [self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES]
        ids_param = ",".join(crypto_ids)
        
        url = f"{self.config.COINGECKO_URL}?ids={ids_param}&vs_currencies=usd"
        
        try:
            data = self._make_request(url)
            rates = {}
            
            for crypto_code in self.config.CRYPTO_CURRENCIES:
                crypto_id = self.config.CRYPTO_ID_MAP[crypto_code]
                if crypto_id in data and "usd" in data[crypto_id]:
                    rate_key = f"{crypto_code}_{self.config.BASE_CURRENCY}"
                    rates[rate_key] = data[crypto_id]["usd"]
            
            self.logger.info(f"Fetched {len(rates)} crypto rates")
            return rates
            
        except ApiRequestError:
            self.logger.error("Failed to fetch crypto rates")
            raise


class ExchangeRateApiClient(BaseApiClient):

    """клиент для ExchangeRate-API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """получает курсы фиатных валют"""
        self.logger.info("Fetching fiat rates from ExchangeRate-API")
        
        if not self.config.EXCHANGERATE_API_KEY:
            self.logger.warning("ExchangeRate-API key not configured")
            return {}
        
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
        
        try:
            data = self._make_request(url)
            
            if data.get("result") != "success":
                raise ApiRequestError(f"API error: {data.get('error-type', 'Unknown error')}")
            
            rates = {}

            available_currencies = list(data.get("conversion_rates", {}).keys())
            self.logger.info(f"Available currencies from API: {len(available_currencies)} currencies")

            for currency in self.config.FIAT_CURRENCIES:
                if currency in data.get("conversion_rates", {}):
                    rate_key = f"{currency}_{self.config.BASE_CURRENCY}"
                    rates[rate_key] = data["conversion_rates"][currency]
            
            self.logger.info(f"Fetched {len(rates)} fiat rates")
            return rates
            
        except ApiRequestError:
            self.logger.error("Failed to fetch fiat rates")
            raise