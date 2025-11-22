import functools
import logging
from datetime import datetime
from typing import Any, Callable, Dict


def log_action(action_name: str = None, verbose: bool = False):
    """
    декоратор для логирования ключевых операций
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger('actions')
            
            operation = action_name or func.__name__.upper()
            
            log_data = {
                'action': operation,
                'timestamp': datetime.now().isoformat(),
            }
            
            try:
                if len(args) > 1 and hasattr(args[0], 'user_manager'):
                    user_manager = args[0].user_manager
                    if hasattr(user_manager, 'current_user') and user_manager.current_user:
                        log_data['username'] = user_manager.current_user.username
                        log_data['user_id'] = user_manager.current_user.user_id
                
                if 'currency_code' in kwargs:
                    log_data['currency_code'] = kwargs['currency_code']
                if 'amount' in kwargs:
                    log_data['amount'] = kwargs['amount']
                
                result = func(*args, **kwargs)
                
                log_data['result'] = 'OK'
                
                if verbose and result:
                    if 'rate' in result:
                        log_data['rate'] = result.get('rate')
                    if 'estimated_cost' in result:
                        log_data['estimated_cost'] = result.get('estimated_cost')
                    if 'estimated_revenue' in result:
                        log_data['estimated_revenue'] = result.get('estimated_revenue')
                    if 'old_balance' in result and 'new_balance' in result:
                        log_data['balance_change'] = f"{result['old_balance']:.4f}→{result['new_balance']:.4f}"
                
                log_message = _format_log_message(log_data)
                logger.info(log_message)
                
                return result
                
            except Exception as e:
                log_data['result'] = 'ERROR'
                log_data['error_type'] = type(e).__name__
                log_data['error_message'] = str(e)
                
                log_message = _format_log_message(log_data)
                logger.error(log_message)
                
                raise
        
        return wrapper
    
    return decorator

def _format_log_message(log_data: Dict[str, Any]) -> str:
    """форматирование в читаемую строку"""
    parts = [f"{log_data['action']}"]
    
    if 'username' in log_data:
        parts.append(f"user='{log_data['username']}'")
    
    if 'currency_code' in log_data:
        parts.append(f"currency='{log_data['currency_code']}'")
    
    if 'amount' in log_data:
        parts.append(f"amount={log_data['amount']:.4f}")
    
    if 'rate' in log_data and log_data['rate']:
        parts.append(f"rate={log_data['rate']:.2f}")
    
    if 'estimated_cost' in log_data and log_data['estimated_cost']:
        parts.append(f"cost={log_data['estimated_cost']:.2f}")
    
    if 'estimated_revenue' in log_data and log_data['estimated_revenue']:
        parts.append(f"revenue={log_data['estimated_revenue']:.2f}")
    
    if 'balance_change' in log_data:
        parts.append(f"balance={log_data['balance_change']}")
    
    parts.append(f"result={log_data['result']}")
    
    if log_data['result'] == 'ERROR':
        parts.append(f"error={log_data['error_type']}:{log_data['error_message']}")
    
    return " ".join(parts)