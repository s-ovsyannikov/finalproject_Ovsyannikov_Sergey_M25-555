from datetime import datetime
from ..core.utils import DataManager, ExchangeRateService
from ..core.usecases import UserManager, PortfolioManager


class TradingCLI:
    def __init__(self):
        self.data_manager = DataManager()
        self.rate_service = ExchangeRateService(self.data_manager)
        self.user_manager = UserManager(self.data_manager)
        self.portfolio_manager = PortfolioManager(self.data_manager, self.rate_service)

    def run(self):
        
        self._print_welcome()
        
        while True:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue
                    
                if command == "exit":
                    break
                elif command.startswith("register"):
                    self._handle_register(command)
                elif command.startswith("login"):
                    self._handle_login(command)
                elif command.startswith("show-portfolio"):
                    self._handle_show_portfolio(command)
                elif command.startswith("buy"):
                    self._handle_buy(command)
                elif command.startswith("sell"):
                    self._handle_sell(command)
                elif command.startswith("get-rate"):
                    self._handle_get_rate(command)
                elif command == "help":
                    self._print_help()
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except Exception as e:
                print(f"Error: {e}")

    def _print_welcome(self):
        print("=== ValutaTrade Hub ===")
        print("Available commands: register, login, show-portfolio, buy, sell, get-rate, help, exit")


    def _print_help(self):
        help_text = """
Available commands:

register --username <username> --password <password>
    Register new user

login --username <username> --password <password>
    Login to system

show-portfolio [--base <currency>]
    Show portfolio with total value

buy --currency <code> --amount <amount>
    Buy currency

sell --currency <code> --amount <amount>
    Sell currency

get-rate --from <currency> --to <currency>
    Get exchange rate

help
    Show this help

exit
    Exit application
"""
        print(help_text)

    def _parse_args(self, command: str) -> dict:
        
        args = {}
        parts = command.split()
        i = 1
        while i < len(parts):
            if parts[i].startswith("--"):
                key = parts[i][2:]
                if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                    args[key] = parts[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        return args

    def _handle_register(self, command: str):
        args = self._parse_args(command)
        
        username = args.get("username")
        password = args.get("password")
        
        if not username or not password:
            print("Usage: register --username <username> --password <password>")
            return
        
        try:
            user = self.user_manager.register_user(username, password)
            print(f"User '{username}' registered successfully (id={user.user_id}).")
            print(f"Login: login --username {username} --password ****")
        except ValueError as e:
            print(f"Registration failed: {e}")

    def _handle_login(self, command: str):
        args = self._parse_args(command)
        
        username = args.get("username")
        password = args.get("password")
        
        if not username or not password:
            print("Usage: login --username <username> --password <password>")
            return
        
        try:
            user = self.user_manager.login(username, password)
            print(f"Welcome, {username}!")
        except ValueError as e:
            print(f"Login failed: {e}")

    def _handle_show_portfolio(self, command: str):
        if not self.user_manager.current_user:
            print("Please login first")
            return
        
        args = self._parse_args(command)
        base_currency = args.get("base", "USD").upper()
        
        try:
            portfolio = self.portfolio_manager.get_user_portfolio(
                self.user_manager.current_user.user_id
            )
            rates = self.rate_service.get_rates()
            
            print(f"\nPortfolio of user '{self.user_manager.current_user.username}' (base: {base_currency}):")
            print("-" * 50)
            
            total_value = 0
            for currency_code, wallet in portfolio.wallets.items():
                balance = wallet.balance
                
                if currency_code == base_currency:
                    value = balance
                    rate_info = "1.0000"
                else:
                    rate = self.rate_service.get_rate(currency_code, base_currency)
                    if rate:
                        value = balance * rate
                        rate_info = f"{rate:.4f}"
                    else:
                        value = 0
                        rate_info = "N/A"
                
                total_value += value
                print(f"- {currency_code}: {balance:12.4f} → {value:12.4f} {base_currency} (rate: {rate_info})")
            
            print("-" * 50)
            print(f"TOTAL: {total_value:12.4f} {base_currency}")
            
        except Exception as e:
            print(f"Error showing portfolio: {e}")

    def _handle_buy(self, command: str):
        if not self.user_manager.current_user:
            print("Please login first")
            return
        
        args = self._parse_args(command)
        
        currency = args.get("currency")
        amount_str = args.get("amount")
        
        if not currency or not amount_str:
            print("Usage: buy --currency <code> --amount <amount>")
            return
        
        try:
            amount = float(amount_str)
            result = self.portfolio_manager.buy_currency(
                self.user_manager.current_user.user_id,
                currency,
                amount
            )
            
            print(f"Purchase completed: {amount:.4f} {currency}")
            if result["rate"]:
                print(f"Exchange rate: {result['rate']:.4f} {currency}/USD")
                print(f"Estimated cost: {result['estimated_cost']:.2f} USD")
            print(f"New balance: {result['new_balance']:.4f} {currency}")
            
        except (ValueError, TypeError) as e:
            print(f"Purchase failed: {e}")

    def _handle_sell(self, command: str):
        if not self.user_manager.current_user:
            print("Please login first")
            return
        
        args = self._parse_args(command)
        
        currency = args.get("currency")
        amount_str = args.get("amount")
        
        if not currency or not amount_str:
            print("Usage: sell --currency <code> --amount <amount>")
            return
        
        try:
            amount = float(amount_str)
            result = self.portfolio_manager.sell_currency(
                self.user_manager.current_user.user_id,
                currency,
                amount
            )
            
            print(f"Sale completed: {amount:.4f} {currency}")
            if result["rate"]:
                print(f"Exchange rate: {result['rate']:.4f} {currency}/USD")
                print(f"Estimated revenue: {result['estimated_revenue']:.2f} USD")
            print(f"New balance: {result['new_balance']:.4f} {currency}")
            
        except (ValueError, TypeError) as e:
            print(f"Sale failed: {e}")

    def _handle_get_rate(self, command: str):
        args = self._parse_args(command)
        
        from_currency = args.get("from")
        to_currency = args.get("to")
        
        if not from_currency or not to_currency:
            print("Usage: get-rate --from <currency> --to <currency>")
            return
        
        try:
            rate = self.rate_service.get_rate(from_currency.upper(), to_currency.upper())
            if rate:
                rates_data = self.rate_service.get_rates()
                updated_at = rates_data.get("last_refresh", "Unknown")
                
                print(f"Exchange rate {from_currency}→{to_currency}: {rate:.6f}")
                print(f"Reverse rate {to_currency}→{from_currency}: {1/rate:.6f}")
                print(f"Updated: {updated_at}")
            else:
                print(f"Exchange rate {from_currency}→{to_currency} not available")
                
        except Exception as e:
            print(f"Error getting rate: {e}")