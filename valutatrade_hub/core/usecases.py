from typing import Optional, Dict, Any
from datetime import datetime
import secrets
from .models import User, Wallet, Portfolio
from .utils import DataManager, ExchangeRateService


class UserManager:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.current_user: Optional[User] = None

    def register_user(self, username: str, password: str) -> User:
        """регистрация пользователя"""
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters long")
        
        
        users_data = self.data_manager.load_json("users.json", [])
        if any(user["username"] == username for user in users_data):
            raise ValueError(f"Username '{username}' already exists")
        
        user_id = max([user.get("user_id", 0) for user in users_data], default=0) + 1
        
        
        salt = secrets.token_hex(8)
        hashed_password = self._hash_password(password, salt)
        registration_date = datetime.now()
        
        user = User(user_id, username, hashed_password, salt, registration_date)
        
        
        users_data.append({
            "user_id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "salt": salt,
            "registration_date": registration_date.isoformat()
        })
        self.data_manager.save_json("users.json", users_data)
        
        
        self._create_user_portfolio(user_id)
        
        return user

    def login(self, username: str, password: str) -> User:
        
        users_data = self.data_manager.load_json("users.json", [])
        
        for user_data in users_data:
            if user_data["username"] == username:
                
                test_hash = self._hash_password(password, user_data["salt"])
                if test_hash == user_data["hashed_password"]:
                    user = User(
                        user_data["user_id"],
                        user_data["username"],
                        user_data["hashed_password"],
                        user_data["salt"],
                        datetime.fromisoformat(user_data["registration_date"])
                    )
                    self.current_user = user
                    return user
        
        raise ValueError("Invalid username or password")

    def logout(self):
        
        self.current_user = None

    def _create_user_portfolio(self, user_id: int):
        
        portfolios_data = self.data_manager.load_json("portfolios.json", [])
        
        
        if not any(portfolio["user_id"] == user_id for portfolio in portfolios_data):
            portfolios_data.append({
                "user_id": user_id,
                "wallets": {}
            })
            self.data_manager.save_json("portfolios.json", portfolios_data)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        import hashlib
        return hashlib.sha256((password + salt).encode()).hexdigest()


class PortfolioManager:
    def __init__(self, data_manager: DataManager, rate_service: ExchangeRateService):
        self.data_manager = data_manager
        self.rate_service = rate_service

    def get_user_portfolio(self, user_id: int) -> Portfolio:
        
        portfolios_data = self.data_manager.load_json("portfolios.json", [])
        
        for portfolio_data in portfolios_data:
            if portfolio_data["user_id"] == user_id:
                wallets = {}
                for currency_code, wallet_data in portfolio_data.get("wallets", {}).items():
                    wallets[currency_code] = Wallet(
                        currency_code, 
                        wallet_data.get("balance", 0.0)
                    )
                return Portfolio(user_id, wallets)
        
        
        portfolio = Portfolio(user_id)
        self._save_portfolio(portfolio)
        return portfolio

    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        portfolio = self.get_user_portfolio(user_id)
        currency_code = currency_code.upper()
        
        
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        
        
        self._save_portfolio(portfolio)
        
        
        rate = self.rate_service.get_rate(currency_code, "USD")
        estimated_cost = amount * rate if rate else None
        
        return {
            "currency": currency_code,
            "amount": amount,
            "new_balance": wallet.balance,
            "estimated_cost": estimated_cost,
            "rate": rate
        }

    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        portfolio = self.get_user_portfolio(user_id)
        currency_code = currency_code.upper()
        
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            raise ValueError(f"You don't have wallet for currency '{currency_code}'")
        
        wallet.withdraw(amount)
        
        
        self._save_portfolio(portfolio)
        
        
        rate = self.rate_service.get_rate(currency_code, "USD")
        estimated_revenue = amount * rate if rate else None
        
        return {
            "currency": currency_code,
            "amount": amount,
            "new_balance": wallet.balance,
            "estimated_revenue": estimated_revenue,
            "rate": rate
        }

    def _save_portfolio(self, portfolio: Portfolio):
        """Save portfolio to JSON"""
        portfolios_data = self.data_manager.load_json("portfolios.json", [])
        
        
        found = False
        for portfolio_data in portfolios_data:
            if portfolio_data["user_id"] == portfolio.user_id:
                wallets_data = {}
                for currency_code, wallet in portfolio.wallets.items():
                    wallets_data[currency_code] = wallet.get_balance_info()
                portfolio_data["wallets"] = wallets_data
                found = True
                break
        
        
        if not found:
            wallets_data = {}
            for currency_code, wallet in portfolio.wallets.items():
                wallets_data[currency_code] = wallet.get_balance_info()
            
            portfolios_data.append({
                "user_id": portfolio.user_id,
                "wallets": wallets_data
            })
        
        self.data_manager.save_json("portfolios.json", portfolios_data)