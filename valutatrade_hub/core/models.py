import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional

from .exceptions import InsufficientFundsError


class User:
    """класс пользователя системы"""
    def __init__(self, user_id: int, username: str, hashed_password: str, 
                 salt: str, registration_date: datetime):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Username cannot be empty")
        self._username = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def get_user_info(self) -> str:
        return (f"User ID: {self._user_id}, "
                f"Username: {self._username}, "
                f"Registered: {self._registration_date}")

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters long")
        
        new_salt = secrets.token_hex(8)
        new_hashed_password = self._hash_password(new_password, new_salt)
        
        self._hashed_password = new_hashed_password
        self._salt = new_salt

    def verify_password(self, password: str) -> bool:
        test_hash = self._hash_password(password, self._salt)
        return test_hash == self._hashed_password

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"])
        )

class Wallet:
    """класс кошелька пользователя для конкретной валюты"""
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise ValueError("Balance must be a number")
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise InsufficientFundsError(
                self.currency_code, 
                self._balance, 
                amount
            )
        self.balance -= amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self._balance:.4f}"

    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    """класс управления всеми кошельками пользователя"""
    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            raise ValueError(f"Wallet for currency '{currency_code}' already exists")
        
        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        currency_code = currency_code.upper()
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = 'USD', exchange_rates: Optional[Dict] = None) -> float:
        if exchange_rates is None:
            exchange_rates = {}
        
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    rate = exchange_rates[rate_key]["rate"]
                    total_value += wallet.balance * rate
                else:
                    demo_rates = {
                        "BTC_USD": 59337.21,
                        "EUR_USD": 1.0786,
                        "RUB_USD": 0.01016,
                        "ETH_USD": 3720.00
                    }
                    if rate_key in demo_rates:
                        total_value += wallet.balance * demo_rates[rate_key]
        
        return total_value

    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "wallets": {
                currency: wallet.to_dict() 
                for currency, wallet in self._wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        wallets = {
            currency: Wallet.from_dict(wallet_data) 
            for currency, wallet_data in data["wallets"].items()
        }
        return cls(user_id=data["user_id"], wallets=wallets)