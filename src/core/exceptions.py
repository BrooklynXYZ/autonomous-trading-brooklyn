class TradingBotException(Exception):
    pass

class ExchangeConnectionError(TradingBotException):
    pass

class OrderExecutionError(TradingBotException):
    pass
