import logging
from typing import Dict

from ..core.exceptions import ApiRequestError
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import RatesStorage


class RatesUpdater:
    """класс для обновления курсов"""
    
    def __init__(self):
        self.config = ParserConfig()
        self.storage = RatesStorage(self.config)
        self.logger = logging.getLogger('parser')
        
        self.clients = {
            "coingecko": CoinGeckoClient(self.config),
            "exchangerate": ExchangeRateApiClient(self.config)
        }
    
    def run_update(self, source: str = None) -> Dict[str, float]:
        """запускает обновление курсов"""
        self.logger.info("Starting rates update")
        
        all_rates = {}
        sources_to_update = [source] if source else list(self.clients.keys())
        
        for client_name in sources_to_update:
            if client_name not in self.clients:
                self.logger.warning(f"Unknown source: {client_name}")
                continue
            
            try:
                client = self.clients[client_name]
                rates = client.fetch_rates()
                all_rates.update(rates)
                
                for pair, rate in rates.items():
                    from_currency, to_currency = pair.split('_')
                    self.storage.save_historical_record(
                        from_currency, to_currency, rate, client_name.upper(),
                        {"request_ms": 0, "status_code": 200}  # Заглушка для метаданных
                    )
                
                self.logger.info(f"Successfully updated from {client_name}: {len(rates)} rates")
                
            except ApiRequestError as e:
                self.logger.error(f"Failed to update from {client_name}: {e}")
                continue
        
        if all_rates:
            self.storage.save_current_rates(all_rates, "ParserService")
            self.logger.info(f"Update completed. Total rates: {len(all_rates)}")
        else:
            self.logger.warning("No rates were updated")
        
        return all_rates