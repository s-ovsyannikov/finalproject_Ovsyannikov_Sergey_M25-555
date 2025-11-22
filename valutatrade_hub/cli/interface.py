import argparse
from typing import Optional

from ..core.currencies import get_all_currencies
from ..core.exceptions import CurrencyNotFoundError, InsufficientFundsError
from ..core.models import User
from ..core.usecases import PortfolioManager, UserManager
from ..core.utils import DataManager, ExchangeRateService
from ..parser_service.config import ParserConfig
from ..parser_service.storage import RatesStorage
from ..parser_service.updater import RatesUpdater


class CLIInterface:
    def __init__(self):
        self.data_manager = DataManager()
        self.rate_service = ExchangeRateService(self.data_manager)
        self.user_manager = UserManager(self.data_manager)
        self.portfolio_manager = PortfolioManager(self.data_manager, self.rate_service)
        self.current_user: Optional[User] = None
        self.rates_updater = RatesUpdater()
        self.rates_storage = RatesStorage(ParserConfig())
    
    def register(self, args):
        """register - создать нового пользователя"""
        try:
            user = self.user_manager.register_user(args.username, args.password)
            print(f"User '{user.username}' registered (id={user.user_id}). Login: login --username {user.username} --password ****")
        except ValueError as e:
            print(f"Error: {e}")
    
    def login(self, args):
        """login - войти в систему"""
        try:
            self.current_user = self.user_manager.login(args.username, args.password)
            print(f"Logged in as '{self.current_user.username}'")
        except ValueError as e:
            print(f"Error: {e}")
    
    def show_portfolio(self, args):
        """show-portfolio - показать портфель"""
        if not self.current_user:
            print("Error: Please login first")
            return
        
        try:
            portfolio = self.portfolio_manager.get_user_portfolio(self.current_user.user_id)
            
            base_currency = args.base.upper() if args.base else 'USD'
            
            print(f"Portfolio of user '{self.current_user.username}' (base: {base_currency}):")
            
            if not portfolio.wallets:
                print("  Portfolio is empty")
                return
            
            total_value = 0.0
            
            for currency_code, wallet in portfolio.wallets.items():
                balance = wallet.balance
                
                if currency_code == base_currency:
                    value = balance
                    print(f"  - {currency_code}: {balance:.2f} → {value:.2f} {base_currency}")
                else:
                    rate = self.rate_service.get_rate(currency_code, base_currency)
                    if rate:
                        value = balance * rate
                        print(f"  - {currency_code}: {balance:.4f} → {value:.2f} {base_currency} (rate: {rate:.4f})")
                    else:
                        value = 0
                        print(f"  - {currency_code}: {balance:.4f} → rate unavailable")
                
                total_value += value
            
            print("-" * 40)
            print(f"TOTAL: {total_value:,.2f} {base_currency}")
            
        except Exception as e:
            print(f"Error getting portfolio: {e}")
    
    def buy(self, args):
        """buy - купить валюту"""
        if not self.current_user:
            print("Error: Please login first")
            return
        
        try:
            result = self.portfolio_manager.buy_currency(
                self.current_user.user_id, 
                args.currency, 
                args.amount
            )
            
            print(f"Purchase completed: {result['amount']:.4f} {result['currency']}")
            
            if result['rate']:
                print(f"At rate: {result['rate']:.2f} USD/{result['currency']}")
                if result['estimated_cost']:
                    print(f"Estimated cost: {result['estimated_cost']:,.2f} USD")
            
            print("Portfolio changes:")
            print(f"  - {result['currency']}: was {result['old_balance']:.4f} → now {result['new_balance']:.4f}")
            
        except (CurrencyNotFoundError, ValueError) as e:
            print(f"Error: {e}")
    
    def sell(self, args):
        """sell - продать валюту"""
        if not self.current_user:
            print("Error: Please login first")
            return
        
        try:
            result = self.portfolio_manager.sell_currency(
                self.current_user.user_id, 
                args.currency, 
                args.amount
            )
            
            print(f"Sale completed: {result['amount']:.4f} {result['currency']}")
            
            if result['rate']:
                print(f"At rate: {result['rate']:.2f} USD/{result['currency']}")
                if result['estimated_revenue']:
                    print(f"Estimated revenue: {result['estimated_revenue']:,.2f} USD")
            
            print("Portfolio changes:")
            print(f"  - {result['currency']}: was {result['old_balance']:.4f} → now {result['new_balance']:.4f}")
            
        except (CurrencyNotFoundError, InsufficientFundsError, ValueError) as e:
            print(f"Error: {e}")
    
    def get_rate(self, args):
        """get-rate - получить курс валюты"""
        try:
            from_currency = args.from_currency.upper()
            to_currency = args.to_currency.upper()
            
            rate = self.rate_service.get_rate(from_currency, to_currency)
            
            if rate:
                rates = self.rate_service.get_rates()
                updated_at = rates.get("last_refresh", "unknown")
                
                print(f"Rate {from_currency}→{to_currency}: {rate:.6f} (updated: {updated_at})")
                
                reverse_rate = 1.0 / rate if rate != 0 else 0
                print(f"Reverse rate {to_currency}→{from_currency}: {reverse_rate:.6f}")
            else:
                print(f"Rate {from_currency}→{to_currency} unavailable. Try again later.")
                
        except Exception as e:
            print(f"Error getting rate: {e}")
    
    def list_currencies(self, args):
        """list-currencies - показать список валют"""
        currencies = get_all_currencies()
        
        print("Supported currencies:")
        print("-" * 80)
        
        fiats = []
        cryptos = []
        
        for currency in currencies.values():
            if hasattr(currency, 'issuing_country'):
                fiats.append(currency)
            else:
                cryptos.append(currency)
        
        if fiats:
            print("\nFiat currencies:")
            for currency in fiats:
                print(f"  {currency.get_display_info()}")
        
        if cryptos:
            print("\nCryptocurrencies:")
            for currency in cryptos:
                print(f"  {currency.get_display_info()}")
    
    def update_rates(self, args):
        """update-rates - обновление курсов валют"""
        try:
            source = args.source.lower() if args.source else None
            rates = self.rates_updater.run_update(source)

            if rates:
                print(f"Update successful. Total rates updated: {len(rates)}")

                current_data = self.rates_storage.load_current_rates()
                if current_data.get("last_refresh"):
                    print(f"Last refresh: {current_data['last_refresh']}")
            else:
                print("No rates were updated. Check logs for details.")
        except Exception as e:
            print(f"Update failed: {e}")

    def show_rates(self, args):
        """show-rates - показать курсы из кэша"""
        try:
            current_data = self.rates_storage.load_current_rates()
            
            if not current_data.get("pairs"):
                print("Local rates cache is empty. Run 'update-rates' to load data.")
                return
            
            pairs = current_data["pairs"]
            filtered_pairs = {}
            
            if args.currency:
                currency = args.currency.upper()
                for pair, data in pairs.items():
                    if pair.startswith(currency + "_") or pair.endswith("_" + currency):
                        filtered_pairs[pair] = data
            else:
                filtered_pairs = pairs
            
            sorted_pairs = sorted(filtered_pairs.items(), 
                                key=lambda x: x[1]["rate"], 
                                reverse=True)
            
            if args.top:
                sorted_pairs = sorted_pairs[:args.top]
            
            print(f"Rates from cache (updated at {current_data.get('last_refresh', 'unknown')}):")
            for pair, data in sorted_pairs:
                print(f"- {pair}: {data['rate']} (source: {data.get('source', 'unknown')})")
                
        except Exception as e:
            print(f"Error showing rates: {e}")   


    def _parse_input(self, user_input: str):
        """парсинг ввода пользователя в аргументы"""
        import shlex
        try:
            parts = shlex.split(user_input)
            if not parts:
                return None
            
            command = parts[0]
            args_list = parts[1:]
            
            parser = self._create_parser_for_command(command)
            if not parser:
                return None
                
            return parser.parse_args(args_list)
        except (ValueError, SystemExit):
            return None
    
    def _create_parser_for_command(self, command: str):
        """парсинг для конкретной команды"""
        parser = argparse.ArgumentParser(prog=command, add_help=False)
        
        if command == "register":
            parser.add_argument('--username', required=True)
            parser.add_argument('--password', required=True)
        elif command == "login":
            parser.add_argument('--username', required=True)
            parser.add_argument('--password', required=True)
        elif command == "show-portfolio":
            parser.add_argument('--base', required=False)
        elif command == "buy":
            parser.add_argument('--currency', required=True)
            parser.add_argument('--amount', type=float, required=True)
        elif command == "sell":
            parser.add_argument('--currency', required=True)
            parser.add_argument('--amount', type=float, required=True)
        elif command == "get-rate":
            parser.add_argument('--from', dest='from_currency', required=True)
            parser.add_argument('--to', dest='to_currency', required=True)
        elif command == "update-rates":
            parser.add_argument('--source', required=False)
        elif command == "show-rates":
            parser.add_argument('--currency', required=False)
            parser.add_argument('--top', type=int, required=False)
            parser.add_argument('--base', required=False)
        elif command == "list-currencies":
            pass
        else:
            return None
            
        return parser
    
    def _print_help(self):
        """справочная информация по командам"""
        print("\nAvailable commands:")
        print("  register --username <username> --password <password>")
        print("  login --username <username> --password <password>")
        print("  show-portfolio [--base <currency>]")
        print("  buy --currency <code> --amount <amount>")
        print("  sell --currency <code> --amount <amount>")
        print("  get-rate --from <currency> --to <currency>")
        print("  update-rates [--source <coingecko|exchangerate>]")
        print("  show-rates [--currency <code>] [--top <N>] [--base <currency>]")
        print("  list-currencies")
        print("  help")
        print("  exit")
        print("\nExamples:")
        print("  register --username alice --password 1234")
        print("  buy --currency BTC --amount 0.05")
        print("  get-rate --from USD --to BTC")
        print("  update-rates --source coingecko")
        print("  show-rates --top 3")
    
    def run(self):
        """запуск интерфейса"""
        print("=== ValutaTrade Hub ===")
        print("Type 'help' for available commands, 'exit' to quit")
        
        while True:
            try:
                prompt = "valutatrade"
                if self.current_user:
                    prompt = f"valutatrade[{self.current_user.username}]"
                
                user_input = input(f"\n{prompt}> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self._print_help()
                    continue
                
                args = self._parse_input(user_input)
                if not args:
                    print(f"Unknown command or invalid arguments: {user_input}")
                    print("Type 'help' for available commands")
                    continue
                
                command_parts = user_input.split()
                command = command_parts[0].replace('-', '_')
                
                if hasattr(self, command):
                    command_method = getattr(self, command)
                    command_method(args)
                else:
                    print(f"Unknown command: {command_parts[0]}")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")