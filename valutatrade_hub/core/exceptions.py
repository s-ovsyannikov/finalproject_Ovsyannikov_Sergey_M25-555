class TradingBaseError(Exception):
    """базовое исключение"""
    pass


class InsufficientFundsError(TradingBaseError):
    """недостаточно средств"""
    
    def __init__(self, currency_code: str, available: float, required: float):
        self.currency_code = currency_code
        self.available = available
        self.required = required
        super().__init__(f"Insufficient funds: available {available} {currency_code}, required {required} {currency_code}")


class CurrencyNotFoundError(TradingBaseError):
    """неизвестная валюта"""
    
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Unknown currency '{currency_code}'")


class ApiRequestError(TradingBaseError):
    """ошибка при обращении к внешнему API"""
    
    def __init__(self, reason: str = "Unknown error"):
        self.reason = reason
        super().__init__(f"Error when accessing external API: {reason}")