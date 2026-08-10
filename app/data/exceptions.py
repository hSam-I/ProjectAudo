class DataProviderError(Exception):
    """
    Raised when a market data provider fails to fetch data
    (network error, rate limit, exchange rejection, ...).
    """
