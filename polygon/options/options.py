# ========================================================= #
from .. import base_client
from typing import Union
from os import cpu_count
import datetime
try:
    import orjson as json_lib
except ImportError:
    import json as json_lib


# ========================================================= #


# Functions for option symbol parsing and creation

def build_option_symbol(underlying_symbol: str, expiry, call_or_put, strike_price, prefix_o: bool = False):
    """
    Build the option symbol from the details provided.

    :param underlying_symbol: The underlying stock ticker symbol.
    :param expiry: The expiry date for the option. You can pass this argument as ``datetime.datetime`` or
                   ``datetime.date`` object. Or a string in format: ``YYMMDD``. Using datetime objects is recommended.
    :param call_or_put: The option type. You can specify: ``c`` or ``call`` or ``p`` or ``put``. Capital letters are
                        also supported.
    :param strike_price: The strike price for the option. ALWAYS pass this as one number. ``145``, ``240.5``,
                         ``15.003``, ``56``, ``129.02`` are all valid values. It shouldn't have more than three
                         numbers after decimal point.
    :param prefix_o: Whether or not to prefix the symbol with 'O:'. It is needed by polygon endpoints. However all the
                     library functions will automatically add this prefix if you pass in symbols without this prefix.
    :return: The option symbol in the format specified by polygon
    """

    if isinstance(expiry, (datetime.datetime, datetime.date)):
        expiry = expiry.strftime('%y%m%d')

    elif isinstance(expiry, str) and len(expiry) != 6:
        raise ValueError('Expiry string must have 6 characters. Format is: YYMMDD')

    call_or_put = 'C' if call_or_put.lower() in ['c', 'call'] else 'P'

    if '.' in str(strike_price):
        strike, strike_dec = str(strike_price).split('.')[0].rjust(5, '0'), str(
            strike_price).split('.')[1].ljust(3, '0')[:3]
    else:
        strike, strike_dec = str(int(strike_price)).rjust(5, '0'), '000'

    if prefix_o:
        return f'O:{underlying_symbol.upper()}{expiry}{call_or_put}{strike}{strike_dec}'

    return f'{underlying_symbol.upper()}{expiry}{call_or_put}{strike}{strike_dec}'


def parse_option_symbol(option_symbol: str, output_format='object', expiry_format='date'):
    """
    Function to parse an option symbol.

    :param option_symbol: the symbol you want to parse. Both ``TSLA211015P125000`` and ``O:TSLA211015P125000`` are valid
    :param output_format: Output format of the result. defaults to object. Set it to ``dict`` or ``list`` as needed.
    :param expiry_format: The format for the expiry date in the results. Defaults to ``date`` object. change this
                          param to ``string`` to get the value as a string: ``YYYY-MM-DD``
    :return: The parsed values either as an object, list or a dict as indicated by ``output_format``.
    """

    _obj = OptionSymbol(option_symbol, expiry_format)

    if output_format in ['list', list]:
        _obj = [_obj.underlying_symbol, _obj.expiry, _obj.call_or_put, _obj.strike_price, _obj.option_symbol]

    elif output_format in ['dict', dict]:
        _obj = {'underlying_symbol': _obj.underlying_symbol,
                'strike_price': _obj.strike_price,
                'expiry': _obj.expiry,
                'call_or_put': _obj.call_or_put,
                'option_symbol': _obj.option_symbol}

    return _obj


def build_option_symbol_for_tda(underlying_symbol: str, expiry, call_or_put, strike_price,
                                format_: str = 'underscore'):
    """
    Only use this function if you need to create option symbol for TD ameritrade API. This function is just a bonus.

    :param underlying_symbol: The underlying stock ticker symbol.
    :param expiry: The expiry date for the option. You can pass this argument as ``datetime.datetime`` or
                   ``datetime.date`` object. Or a string in format: ``MMDDYY``. Using datetime objects is recommended.
    :param call_or_put: The option type. You can specify: ``c`` or ``call`` or ``p`` or ``put``. Capital letters are
                        also supported.
    :param strike_price: The strike price for the option. ALWAYS pass this as one number. ``145``, ``240.5``,
                         ``15.003``, ``56``, ``129.02`` are all valid values. It shouldn't have more than three
                         numbers after decimal point.
    :param format_: tda has two formats. one having an underscore in between (used by TDA API). and other starts with a
                    dot (``.``). Defaults to the underscore format. **If you're not sure, leave to default.** Pass
                    ``'dot'`` to get dot format.
    :return: The option symbol built in the format supported by TD Ameritrade.
    """

    if isinstance(expiry, (datetime.date, datetime.datetime)):
        expiry = expiry.strftime('%m%d%y')

    call_or_put = 'C' if call_or_put.lower() in ['c', 'call'] else 'P'

    strike_price = int(float(strike_price)) if int(float(strike_price)) == float(strike_price) else strike_price

    if format_ == 'dot':
        return f'.{underlying_symbol}{expiry}{call_or_put}{strike_price}'

    return f'{underlying_symbol}_{expiry}{call_or_put}{strike_price}'


def parse_option_symbol_from_tda(option_symbol: str, output_format='object', expiry_format='date'):
    """
    Function to parse an option symbol in format supported by TD Ameritrade.

    :param option_symbol: the symbol you want to parse. Both ``TSLA211015P125000`` and ``O:TSLA211015P125000`` are valid
    :param output_format: Output format of the result. defaults to object. Set it to ``dict`` or ``list`` as needed.
    :param expiry_format: The format for the expiry date in the results. Defaults to ``date`` object. change this
                          param to ``string`` to get the value as a string: ``YYYY-MM-DD``
    :return: The parsed values either as an object, list or a dict as indicated by ``output_format``.
    """

    format_ = 'underscore'
    if option_symbol.startswith('.'):
        format_ = 'dot'

    _obj = OptionSymbol(option_symbol, expiry_format, symbol_format='tda', fmt=format_)

    if output_format in ['list', list]:
        _obj = [_obj.underlying_symbol, _obj.expiry, _obj.call_or_put, _obj.strike_price, _obj.option_symbol]

    elif output_format in ['dict', dict]:
        _obj = {'underlying_symbol': _obj.underlying_symbol,
                'strike_price': _obj.strike_price,
                'expiry': _obj.expiry,
                'call_or_put': _obj.call_or_put,
                'option_symbol': _obj.option_symbol}

    return _obj


def convert_from_tda_to_polygon_format(option_symbol: str, prefix_o: bool = False):
    """
    Helper function to convert from TD Ameritrade symbol format to polygon format. Useful for writing applications
    which make use of both the APIs

    :param option_symbol: The option symbol. This must be in the format supported by TD Ameritrade
    :param prefix_o: Whether or not to add the prefix O: in front of created symbol
    :return: The formatted symbol converted to polygon's symbol format.
    """

    format_ = 'underscore'
    if option_symbol.startswith('.'):
        format_ = 'dot'

    _temp = OptionSymbol(option_symbol, symbol_format='tda', fmt=format_)

    return build_option_symbol(_temp.underlying_symbol, _temp.expiry, _temp.call_or_put, _temp.strike_price,
                               prefix_o=prefix_o)


def convert_from_polygon_to_tda_format(option_symbol: str, format_: str = 'underscore'):
    """
    Helper function to convert from polygon.io symbol format to TD Ameritrade symbol format. Useful for writing
    applications which make use of both the APIs

    :param option_symbol: The option symbol. This must be in the format supported by polygon.io
    :param format_: tda has two formats. one having an underscore in between (used by TDA API). and other starts with a
                    dot (``.``). Defaults to the underscore format. **If you're not sure, leave to default.** Pass
                    ``'dot'`` to get dot format.
    :return: The formatted symbol converted to TDA symbol format.
    """

    _temp = OptionSymbol(option_symbol)

    return build_option_symbol_for_tda(_temp.underlying_symbol, _temp.expiry, _temp.call_or_put, _temp.strike_price,
                                       format_=format_)


def detect_symbol_format(option_symbol: str) -> Union[str, bool]:
    """
    Detect what format a symbol is formed in. Returns ``polygon`` or ``tda`` depending on which format the symbol is
    in. Returns False if the format doesn't match any of the two supported.

    :param option_symbol: The option symbol to check.
    :return: ``tda`` or ``polygon`` if format is recognized. ``False`` otherwise.
    """
    if option_symbol.startswith('.') or ('_' in option_symbol):
        return 'tda'

    if option_symbol.startswith('O:') or len(option_symbol) > 15:
        return 'polygon'

    return False

# ========================================================= #


def OptionsClient(api_key: str, use_async: bool = False, connect_timeout: int = 10, read_timeout: int = 10,
                    pool_timeout: int = 10, max_connections: int = None, max_keepalive: int = None,
                    write_timeout: int = 10):
    """
    Initiates a Client to be used to access all REST options endpoints.

    :param api_key: Your API Key. Visit your dashboard to get yours.
    :param use_async: Set it to ``True`` to get async client. Defaults to usual non-async client.
    :param connect_timeout: The connection timeout in seconds. Defaults to 10. basically the number of seconds to
                            wait for a connection to be established. Raises a ``ConnectTimeout`` if unable to
                            connect within specified time limit.
    :param read_timeout: The read timeout in seconds. Defaults to 10. basically the number of seconds to wait for
                         date to be received. Raises a ``ReadTimeout`` if unable to connect within the specified
                         time limit.
    :param pool_timeout: The pool timeout in seconds. Defaults to 10. Basically the number of seconds to wait while
                             trying to get a connection from connection pool. Do NOT change if you're unsure of what it
                             implies
    :param max_connections: Max number of connections in the pool. Defaults to NO LIMITS. Do NOT change if you're
                            unsure of application
    :param max_keepalive: max number of allowable keep alive connections in the pool. Defaults to no limit.
                          Do NOT change if you're unsure of the applications.
    :param write_timeout: The write timeout in seconds. Defaults to 10. basically the number of seconds to wait for
                         data to be written/posted. Raises a ``WriteTimeout`` if unable to connect within the
                         specified time limit.
    """

    if not use_async:
        return SyncOptionsClient(api_key, connect_timeout, read_timeout)

    return AsyncOptionsClient(api_key, connect_timeout, read_timeout, pool_timeout, max_connections,
                              max_keepalive, write_timeout)


# ========================================================= #


class SyncOptionsClient(base_client.BaseClient):
    """
    These docs are not meant for general users. These are library API references. The actual docs will be
    available on the index page when they are prepared.

    This class implements all the Options REST endpoints. Note that you should always import names from top level.
    eg: ``from polygon import OptionsClient`` or ``import polygon`` (which allows you to access all names easily)
    """

    def __init__(self, api_key: str, connect_timeout: int = 10, read_timeout: int = 10):
        super().__init__(api_key, connect_timeout, read_timeout)

    # Endpoints
    def get_trades(self, option_symbol: str, timestamp=None, timestamp_lt=None, timestamp_lte=None,
                   timestamp_gt=None, timestamp_gte=None, sort='timestamp', limit: int = 5000, order='asc',
                   all_pages: bool = False, max_pages: int = None, merge_all_pages: bool = True,
                   verbose: bool = False, raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get trades for an options ticker symbol in a given time range. Note that you need to have an option symbol in
        correct format for this endpoint. You can use ``ReferenceClient.get_option_contracts`` to query option contracts
        using many filter parameters such as underlying symbol etc.
        `Official Docs <https://polygon.io/docs/options/get_v3_trades__optionsticker>`__

        :param option_symbol: The options ticker symbol to get trades for. for eg ``O:TSLA210903C00700000``. you can
                              pass the symbol with or without the prefix ``O:``
        :param timestamp: Query by trade timestamp. You can supply a ``date``, ``datetime`` object or a ``nanosecond
                          UNIX timestamp`` or a string in format: ``YYYY-MM-DD``.
        :param timestamp_lt: return results where timestamp is less than the given value. Can be date or date string or
                             nanosecond timestamp
        :param timestamp_lte: return results where timestamp is less than/equal to the given value. Can be date or date
                              string or nanosecond timestamp
        :param timestamp_gt: return results where timestamp is greater than the given value. Can be date or date
                             string or nanosecond timestamp
        :param timestamp_gte: return results where timestamp is greater than/equal to the given value. Can be date or
                              date string or nanosecond timestamp
        :param sort: Sort field used for ordering. Defaults to timestamp. See :class:`polygon.enums.OptionTradesSort`
                     for available choices.
        :param limit: Limit the number of results returned. Defaults to 5000. max is 50000.
        :param order: order of the results. Defaults to ``asc``. See :class:`polygon.enums.SortOrder` for info and
                      available choices.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        timestamp = self.normalize_datetime(timestamp, output_type='nts', unit='ns')

        timestamp_lt = self.normalize_datetime(timestamp_lt, output_type='nts', unit='ns')

        timestamp_lte = self.normalize_datetime(timestamp_lte, output_type='nts', unit='ns')

        timestamp_gt = self.normalize_datetime(timestamp_gt, output_type='nts', unit='ns')

        timestamp_gte = self.normalize_datetime(timestamp_gte, output_type='nts', unit='ns')

        _path = f'/v3/trades/{ensure_prefix(option_symbol)}'

        _data = {'timestamp': timestamp, 'timestamp.lt': timestamp_lt, 'timestamp.lte': timestamp_lte,
                 'timestamp.gt': timestamp_gt, 'timestamp.gte': timestamp_gte, 'order': order, 'sort': sort,
                 'limit': limit}

        _res = self._get_response(_path, params=_data)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                              raw_page_responses=raw_page_responses)

    def get_quotes(self, option_symbol: str, timestamp=None, timestamp_lt=None, timestamp_lte=None,
                   timestamp_gt=None, timestamp_gte=None, sort='timestamp', limit: int = 5000, order='asc',
                   all_pages: bool = False, max_pages: int = None, merge_all_pages: bool = True,
                   verbose: bool = False, raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get quotes for an options ticker symbol in a given time range. Note that you need to have an option symbol in
        correct format for this endpoint. You can use ``ReferenceClient.get_option_contracts`` to query option contracts
        using many filter parameters such as underlying symbol etc.
        `Official Docs <https://polygon.io/docs/options/get_v3_quotes__optionsticker>`__

        :param option_symbol: The options ticker symbol to get quotes for. for eg ``O:TSLA210903C00700000``. you can
                              pass the symbol with or without the prefix ``O:``
        :param timestamp: Query by quote timestamp. You can supply a ``date``, ``datetime`` object or a ``nanosecond
                          UNIX timestamp`` or a string in format: ``YYYY-MM-DD``.
        :param timestamp_lt: return results where timestamp is less than the given value. Can be date or date string or
                             nanosecond timestamp
        :param timestamp_lte: return results where timestamp is less than/equal to the given value. Can be date or date
                              string or nanosecond timestamp
        :param timestamp_gt: return results where timestamp is greater than the given value. Can be date or date
                             string or nanosecond timestamp
        :param timestamp_gte: return results where timestamp is greater than/equal to the given value. Can be date or
                              date string or nanosecond timestamp
        :param sort: Sort field used for ordering. Defaults to timestamp. See :class:`polygon.enums.OptionQuotesSort`
                     for available choices.
        :param limit: Limit the number of results returned. Defaults to 5000. max is 50000.
        :param order: order of the results. Defaults to ``asc``. See :class:`polygon.enums.SortOrder` for info and
                      available choices.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        timestamp = self.normalize_datetime(timestamp, output_type='nts', unit='ns')

        timestamp_lt = self.normalize_datetime(timestamp_lt, output_type='nts', unit='ns')

        timestamp_lte = self.normalize_datetime(timestamp_lte, output_type='nts', unit='ns')

        timestamp_gt = self.normalize_datetime(timestamp_gt, output_type='nts', unit='ns')

        timestamp_gte = self.normalize_datetime(timestamp_gte, output_type='nts', unit='ns')

        _path = f'/v3/quotes/{ensure_prefix(option_symbol)}'

        _data = {'timestamp': timestamp, 'timestamp.lt': timestamp_lt, 'timestamp.lte': timestamp_lte,
                 'timestamp.gt': timestamp_gt, 'timestamp.gte': timestamp_gte, 'order': order, 'sort': sort,
                 'limit': limit}

        _res = self._get_response(_path, params=_data)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                              raw_page_responses=raw_page_responses)

    def get_last_trade(self, ticker: str, raw_response: bool = False):
        """
        Get the most recent trade for a given options contract.
        `Official Docs <https://polygon.io/docs/options/get_v2_last_trade__optionsticker>`__

        :param ticker: The ticker symbol of the options contract. Eg: ``O:TSLA210903C00700000``
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary.
        :return: Either a Dictionary or a Response object depending on value of ``raw_response``. Defaults to Dict.
        """

        _path = f'/v2/last/trade/{ensure_prefix(ticker)}'

        _res = self._get_response(_path)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)

    def get_daily_open_close(self, symbol: str, date, adjusted: bool = True,
                             raw_response: bool = False):
        """
        Get the OCHLV and after-hours prices of a contract on a certain date.
        `Official Docs <https://polygon.io/docs/options/get_v1_open-close__optionsticker___date>`__

        :param symbol: The option symbol we want daily-OCHLV for. eg ``O:FB210903C00700000``. You can pass it with or
                       without the prefix ``O:``
        :param date: The date/day of the daily-OCHLV to retrieve. Could be ``datetime`` or ``date`` or string
                     ``YYYY-MM-DD``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted. Set this
                         to false to get results that are NOT adjusted for splits.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object
        """

        date = self.normalize_datetime(date, output_type='str')

        _path = f'/v1/open-close/{ensure_prefix(symbol)}/{date}'

        _data = {'adjusted': 'true' if adjusted else 'false'}

        _res = self._get_response(_path, params=_data)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)

    def get_aggregate_bars(self, symbol: str, from_date, to_date, adjusted: bool = True,
                           sort='asc', limit: int = 5000, multiplier: int = 1, timespan='day', full_range: bool = False,
                           run_parallel: bool = True, max_concurrent_workers: int = cpu_count() * 5,
                           warnings: bool = True, high_volatility: bool = False, raw_response: bool = False):
        """
        Get aggregate bars for an option contract over a given date range in custom time window sizes.
        For example, if ``timespan = ‘minute’`` and ``multiplier = ‘5’`` then 5-minute bars will be returned.
        `Official Docs
        <https://polygon.io/docs/options/get_v2_aggs_ticker__optionsticker__range__multiplier___timespan___from___to>`__

        :param symbol: The ticker symbol of the contract. eg ``O:FB210903C00700000``. You can pass in with or without
                       the prefix ``O:``
        :param from_date: The start of the aggregate time window. Could be ``datetime`` or ``date`` or string
                          ``YYYY-MM-DD``
        :param to_date: The end of the aggregate time window. Could be ``datetime`` or ``date`` or string ``YYYY-MM-DD``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted. Set this
                         to false to get results that are NOT adjusted for splits.
        :param sort: Sort the results by timestamp. See :class:`polygon.enums.SortOrder` for choices. ``asc`` default.
        :param limit: Limits the number of base aggregates queried to create the aggregate results. Max 50000 and
                      Default 5000. see `this article <https://polygon.io/blog/aggs-api-updates/>`__ for more info.
        :param multiplier: The size of the timespan multiplier. Must be a positive whole number. defaults to 1.
        :param timespan: The size of the time window. See :class:`polygon.enums.Timespan` for choices. defaults to
                         ``day``
        :param full_range: Default False. If set to True, it will get the ENTIRE range you specify and **merge** all
                           the responses and return ONE single list with all data in it. You can control its behavior
                           with the next few arguments.
        :param run_parallel: Only considered if ``full_range=True``. If set to true (default True), it will run an
                             internal ThreadPool to get the responses. This is fine to do if you are not running your
                             own ThreadPool. If you have many tickers to get aggs for, it's better to either use the
                             async version of it OR set this to False and spawn threads for each ticker yourself.
        :param max_concurrent_workers: Only considered if ``run_parallel=True``. Defaults to ``your cpu cores * 5``.
                                       controls how many worker threads to use in internal ThreadPool
        :param warnings: Set to False to disable printing warnings if any when fetching the aggs. Defaults to True.
        :param high_volatility: Specifies whether the symbol/security in question is highly volatile which just means
                                having a very high number of trades or being traded for a high duration (eg SPY, 
                                Bitcoin) If set to True, the lib will use a smaller chunk of time to ensure we don't 
                                miss any data due to 50k candle limit. Defaults to False.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. Will be ignored if ``full_range=True``
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If ``full_range=True``, will return a single list with all the candles in it.
        """

        if not full_range:

            from_date = self.normalize_datetime(from_date, output_type='nts')

            to_date = self.normalize_datetime(to_date, output_type='nts', _dir='end')

            if timespan == 'min':
                timespan = 'minute'

            timespan, sort = self._change_enum(timespan, str), self._change_enum(sort, str)

            _path = f'/v2/aggs/ticker/{ensure_prefix(symbol).upper()}/range/{multiplier}/{timespan}/{from_date}/' \
                    f'{to_date}'

            _data = {'adjusted': 'true' if adjusted else 'false',
                     'sort': sort,
                     'limit': limit}

            _res = self._get_response(_path, params=_data)

            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        # The full range agg begins
        if run_parallel:  # Parallel Run
            time_chunks = self.split_date_range(from_date, to_date, timespan, high_volatility=high_volatility)
            return self.get_full_range_aggregates(self.get_aggregate_bars, symbol, time_chunks, run_parallel,
                                                  max_concurrent_workers, warnings, adjusted=adjusted,
                                                  multiplier=multiplier, sort=sort, limit=limit, timespan=timespan)

        # Sequential Run
        time_chunks = [from_date, to_date]
        return self.get_full_range_aggregates(self.get_aggregate_bars, symbol, time_chunks, run_parallel,
                                              max_concurrent_workers, warnings, adjusted=adjusted,
                                              multiplier=multiplier, sort=sort, limit=limit, timespan=timespan)

    def get_snapshot(self, underlying_symbol: str, option_symbol: str, all_pages: bool = False,
                     max_pages: int = None, merge_all_pages: bool = True, verbose: bool = False,
                     raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get the snapshot of an option contract for a stock equity.
        `Official Docs <https://polygon.io/docs/options/get_v3_snapshot_options__underlyingasset___optioncontract>`__

        :param underlying_symbol: The underlying ticker symbol of the option contract. eg ``AMD``
        :param option_symbol: the option symbol. You can use use the :ref:`option_symbols_header` section to make it
                              easy to work with option symbols in polygon or tda formats.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        _path = f'/v3/snapshot/options/{underlying_symbol}/{ensure_prefix(option_symbol)}'

        _res = self._get_response(_path)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                              raw_page_responses=raw_page_responses)

    def get_previous_close(self, ticker: str, adjusted: bool = True,
                           raw_response: bool = False):
        """
        Get the previous day's open, high, low, and close (OHLC) for the specified option contract.
        `Official Docs <https://polygon.io/docs/options/get_v2_aggs_ticker__optionsticker__prev>`__

        :param ticker: The ticker symbol of the options contract. Eg: ``O:TSLA210903C00700000``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted.
                         Set this to false to get results that are NOT adjusted for splits.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary.
        :return: Either a Dictionary or a Response object depending on value of ``raw_response``. Defaults to Dict.
        """

        _path = f'/v2/aggs/ticker/{ensure_prefix(ticker)}/prev'

        _data = {'adjusted': 'true' if adjusted else 'false'}

        _res = self._get_response(_path, params=_data)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)


# ========================================================= #


class AsyncOptionsClient(base_client.BaseAsyncClient):
    """
    These docs are not meant for general users. These are library API references. The actual docs will be
    available on the index page when they are prepared.

    This class implements all the Options REST endpoints for async uses. Note that you should always import names from
    top level. eg: ``from polygon import OptionsClient`` or ``import polygon`` (which allows you to access all names
    easily)
    """

    def __init__(self, api_key: str, connect_timeout: int = 10, read_timeout: int = 10, pool_timeout: int = 10,
                 max_connections: int = None, max_keepalive: int = None, write_timeout: int = 10):
        super().__init__(api_key, connect_timeout, read_timeout, pool_timeout, max_connections, max_keepalive,
                         write_timeout)

    # Endpoints
    async def get_trades(self, option_symbol: str, timestamp=None, timestamp_lt=None, timestamp_lte=None,
                         timestamp_gt=None, timestamp_gte=None, sort='timestamp', limit: int = 5000,
                         order='asc', all_pages: bool = False, max_pages: int = None, merge_all_pages: bool = True,
                         verbose: bool = False, raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get trades for an options ticker symbol in a given time range. Note that you need to have an option
        symbol in correct format for this endpoint. You can use ``ReferenceClient.get_option_contracts`` to query option
        contracts using many filter parameters such as underlying symbol etc.
        `Official Docs <https://polygon.io/docs/options/get_v3_trades__optionsticker>`__

        :param option_symbol: The options ticker symbol to get trades for. for eg ``O:TSLA210903C00700000``. you can
                              pass the symbol with or without the prefix ``O:``
        :param timestamp: Query by trade timestamp. You can supply a ``date``, ``datetime`` object or a ``nanosecond
                          UNIX timestamp`` or a string in format: ``YYYY-MM-DD``.
        :param timestamp_lt: return results where timestamp is less than the given value. Can be date or date string or
                             nanosecond timestamp
        :param timestamp_lte: return results where timestamp is less than/equal to the given value. Can be date or date
                              string or nanosecond timestamp
        :param timestamp_gt: return results where timestamp is greater than the given value. Can be date or date
                             string or nanosecond timestamp
        :param timestamp_gte: return results where timestamp is greater than/equal to the given value. Can be date or
                              date string or nanosecond timestamp
        :param sort: Sort field used for ordering. Defaults to timestamp. See
                     :class:`polygon.enums.OptionTradesSort` for available choices.
        :param limit: Limit the number of results returned. Defaults to 100. max is 50000.
        :param order: order of the results. Defaults to ``asc``. See :class:`polygon.enums.SortOrder` for info and
                      available choices.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        timestamp = self.normalize_datetime(timestamp, output_type='nts', unit='ns')

        timestamp_lt = self.normalize_datetime(timestamp_lt, output_type='nts', unit='ns')

        timestamp_lte = self.normalize_datetime(timestamp_lte, output_type='nts', unit='ns')

        timestamp_gt = self.normalize_datetime(timestamp_gt, output_type='nts', unit='ns')

        timestamp_gte = self.normalize_datetime(timestamp_gte, output_type='nts', unit='ns')

        _path = f'/v3/trades/{ensure_prefix(option_symbol)}'

        _data = {'timestamp': timestamp, 'timestamp.lt': timestamp_lt, 'timestamp.lte': timestamp_lte,
                 'timestamp.gt': timestamp_gt, 'timestamp.gte': timestamp_gte, 'order': order, 'sort': sort,
                 'limit': limit}

        _res = await self._get_response(_path, params=_data)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return await self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                                    raw_page_responses=raw_page_responses)

    async def get_quotes(self, option_symbol: str, timestamp=None, timestamp_lt=None, timestamp_lte=None,
                         timestamp_gt=None, timestamp_gte=None, sort='timestamp', limit: int = 5000, order='asc',
                         all_pages: bool = False, max_pages: int = None, merge_all_pages: bool = True,
                         verbose: bool = False, raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get quotes for an options ticker symbol in a given time range. Note that you need to have an option symbol in
        correct format for this endpoint. You can use ``ReferenceClient.get_option_contracts`` to query option contracts
        using many filter parameters such as underlying symbol etc.
        `Official Docs <https://polygon.io/docs/options/get_v3_quotes__optionsticker>`__

        :param option_symbol: The options ticker symbol to get quotes for. for eg ``O:TSLA210903C00700000``. you can
                              pass the symbol with or without the prefix ``O:``
        :param timestamp: Query by quote timestamp. You can supply a ``date``, ``datetime`` object or a ``nanosecond
                          UNIX timestamp`` or a string in format: ``YYYY-MM-DD``.
        :param timestamp_lt: return results where timestamp is less than the given value. Can be date or date string or
                             nanosecond timestamp
        :param timestamp_lte: return results where timestamp is less than/equal to the given value. Can be date or date
                              string or nanosecond timestamp
        :param timestamp_gt: return results where timestamp is greater than the given value. Can be date or date
                             string or nanosecond timestamp
        :param timestamp_gte: return results where timestamp is greater than/equal to the given value. Can be date or
                              date string or nanosecond timestamp
        :param sort: Sort field used for ordering. Defaults to timestamp. See :class:`polygon.enums.OptionQuotesSort`
                     for available choices.
        :param limit: Limit the number of results returned. Defaults to 5000. max is 50000.
        :param order: order of the results. Defaults to ``asc``. See :class:`polygon.enums.SortOrder` for info and
                      available choices.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        timestamp = self.normalize_datetime(timestamp, output_type='nts', unit='ns')

        timestamp_lt = self.normalize_datetime(timestamp_lt, output_type='nts', unit='ns')

        timestamp_lte = self.normalize_datetime(timestamp_lte, output_type='nts', unit='ns')

        timestamp_gt = self.normalize_datetime(timestamp_gt, output_type='nts', unit='ns')

        timestamp_gte = self.normalize_datetime(timestamp_gte, output_type='nts', unit='ns')

        _path = f'/v3/quotes/{ensure_prefix(option_symbol)}'

        _data = {'timestamp': timestamp, 'timestamp.lt': timestamp_lt, 'timestamp.lte': timestamp_lte,
                 'timestamp.gt': timestamp_gt, 'timestamp.gte': timestamp_gte, 'order': order, 'sort': sort,
                 'limit': limit}

        _res = await self._get_response(_path, params=_data)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return await self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                                    raw_page_responses=raw_page_responses)

    async def get_last_trade(self, ticker: str, raw_response: bool = False):
        """
        Get the most recent trade for a given options contract - Async
        `Official Docs <https://polygon.io/docs/options/get_v2_last_trade__optionsticker>`__

        :param ticker: The ticker symbol of the options contract. Eg: ``O:TSLA210903C00700000``
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say
                             check the status code or inspect the headers. Defaults to False which returns the json
                             decoded dictionary.
        :return: Either a Dictionary or a Response object depending on value of ``raw_response``. Defaults to Dict.
        """

        _path = f'/v2/last/trade/{ensure_prefix(ticker)}'

        _res = await self._get_response(_path)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)

    async def get_daily_open_close(self, symbol: str, date, adjusted: bool = True,
                                   raw_response: bool = False):
        """
        Get the OCHLV and after-hours prices of a contract on a certain date.
        `Official Docs <https://polygon.io/docs/options/get_v1_open-close__optionsticker___date>`__

        :param symbol: The option symbol we want daily-OCHLV for. eg ``O:FB210903C00700000``. You can pass it with or
                       without the prefix ``O:``
        :param date: The date/day of the daily-OCHLV to retrieve. Could be ``datetime`` or ``date`` or string
                     ``YYYY-MM-DD``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted. Set this
                         to false to get results that are NOT adjusted for splits.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object
        """

        date = self.normalize_datetime(date, output_type='str')

        _path = f'/v1/open-close/{ensure_prefix(symbol)}/{date}'

        _data = {'adjusted': 'true' if adjusted else 'false'}

        _res = await self._get_response(_path, params=_data)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)

    async def get_aggregate_bars(self, symbol: str, from_date, to_date, adjusted: bool = True,
                                 sort='asc', limit: int = 5000, multiplier: int = 1, timespan='day',
                                 full_range: bool = False, run_parallel: bool = True,
                                 max_concurrent_workers: int = cpu_count() * 5, warnings: bool = True,
                                 high_volatility: bool = False, raw_response: bool = False):
        """
        Get aggregate bars for an option contract over a given date range in custom time window sizes.
        For example, if ``timespan = ‘minute’`` and ``multiplier = ‘5’`` then 5-minute bars will be returned.
        `Official Docs
        <https://polygon.io/docs/options/get_v2_aggs_ticker__optionsticker__range__multiplier___timespan___from___to>`__

        :param symbol: The ticker symbol of the contract. eg ``O:FB210903C00700000``. You can pass in with or without
                       the prefix ``O:``
        :param from_date: The start of the aggregate time window. Could be ``datetime`` or ``date`` or string
                          ``YYYY-MM-DD``
        :param to_date: The end of the aggregate time window. Could be ``datetime`` or ``date`` or string ``YYYY-MM-DD``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted. Set this
                         to false to get results that are NOT adjusted for splits.
        :param sort: Sort the results by timestamp. See :class:`polygon.enums.SortOrder` for choices. ``asc`` default.
        :param limit: Limits the number of base aggregates queried to create the aggregate results. Max 50000 and
                      Default 5000. see `this article <https://polygon.io/blog/aggs-api-updates/>`__ for more info.
        :param multiplier: The size of the timespan multiplier. Must be a positive whole number. defaults to 1.
        :param timespan: The size of the time window. See :class:`polygon.enums.Timespan` for choices. defaults to
                         ``day``
        :param full_range: Default False. If set to True, it will get the ENTIRE range you specify and **merge** all
                           the responses and return ONE single list with all data in it. You can control its behavior
                           with the next few arguments.
        :param run_parallel: Only considered if ``full_range=True``. If set to true (default True), it will run an
                             internal ThreadPool to get the responses. This is fine to do if you are not running your
                             own ThreadPool. If you have many tickers to get aggs for, it's better to either use the
                             async version of it OR set this to False and spawn threads for each ticker yourself.
        :param max_concurrent_workers: Only considered if ``run_parallel=True``. Defaults to ``your cpu cores * 5``.
                                       controls how many worker threads to use in internal ThreadPool
        :param warnings: Set to False to disable printing warnings if any when fetching the aggs. Defaults to True.
        :param high_volatility: Specifies whether the symbol/security in question is highly volatile which just means
                                having a very high number of trades or being traded for a high duration (eg SPY,
                                Bitcoin) If set to True, the lib will use a smaller chunk of time to ensure we don't
                                miss any data due to 50k candle limit. Defaults to False.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. Will be ignored if ``full_range=True``
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If ``full_range=True``, will return a single list with all the candles in it.
        """

        if not full_range:

            from_date = self.normalize_datetime(from_date, output_type='nts')

            to_date = self.normalize_datetime(to_date, output_type='nts', _dir='end')

            if timespan == 'min':
                timespan = 'minute'

            timespan, sort = self._change_enum(timespan, str), self._change_enum(sort, str)

            _path = f'/v2/aggs/ticker/{ensure_prefix(symbol).upper()}/range/{multiplier}/{timespan}/{from_date}/' \
                    f'{to_date}'

            _data = {'adjusted': 'true' if adjusted else 'false',
                     'sort': sort,
                     'limit': limit}

            _res = await self._get_response(_path, params=_data)

            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        # The full range agg begins
        if run_parallel:  # Parallel Run
            time_chunks = self.split_date_range(from_date, to_date, timespan, high_volatility=high_volatility)
            return await self.get_full_range_aggregates(self.get_aggregate_bars, symbol, time_chunks, run_parallel,
                                                        max_concurrent_workers, warnings, adjusted=adjusted,
                                                        multiplier=multiplier, sort=sort, limit=limit,
                                                        timespan=timespan)

        # Sequential Run
        time_chunks = [from_date, to_date]
        return await self.get_full_range_aggregates(self.get_aggregate_bars, symbol, time_chunks, run_parallel,
                                                    max_concurrent_workers, warnings, adjusted=adjusted,
                                                    multiplier=multiplier, sort=sort, limit=limit,
                                                    timespan=timespan)

    async def get_snapshot(self, underlying_symbol: str, option_symbol: str, all_pages: bool = False,
                           max_pages: int = None, merge_all_pages: bool = True, verbose: bool = False,
                           raw_page_responses: bool = False, raw_response: bool = False):
        """
        Get the snapshot of an option contract for a stock equity.
        `Official Docs <https://polygon.io/docs/options/get_v3_snapshot_options__underlyingasset___optioncontract>`__

        :param underlying_symbol: The underlying ticker symbol of the option contract. eg ``AMD``
        :param option_symbol: the option symbol. You can use use the :ref:`option_symbols_header` section to make it
                              easy to work with option symbols in polygon or tda formats.
        :param all_pages: Whether to paginate through next/previous pages internally. Defaults to False. If set to True,
                          it will try to paginate through all pages and merge all pages internally for you.
        :param max_pages: how many pages to fetch. Defaults to None which fetches all available pages. Change to an
                          integer to fetch at most that many pages. This param is only considered if ``all_pages``
                          is set to True
        :param merge_all_pages: If this is True, returns a single merged response having all the data. If False,
                                returns a list of all pages received. The list can be either a list of response
                                objects or decoded data itself, controlled by parameter ``raw_page_responses``.
                                This argument is Only considered if ``all_pages`` is set to True. Default: True
        :param verbose: Set to True to print status messages during the pagination process. Defaults to False.
        :param raw_page_responses: If this is true, the list of pages will be a list of corresponding Response objects.
                                   Else, it will be a list of actual data for pages. This parameter is only
                                   considered if ``merge_all_pages`` is set to False. Default: False
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say check the
                             status code or inspect the headers. Defaults to False which returns the json decoded
                             dictionary. This is ignored if pagination is set to True.
        :return: A JSON decoded Dictionary by default. Make ``raw_response=True`` to get underlying response object.
                 If pagination is set to True, will return a merged response of all pages for convenience.
        """

        _path = f'/v3/snapshot/options/{underlying_symbol}/{ensure_prefix(option_symbol)}'

        _res = await self._get_response(_path)

        if not all_pages:  # don't you dare paginating!!
            if raw_response:
                return _res

            return json_lib.loads(_res.text)

        return await self._paginate(_res, merge_all_pages, max_pages, verbose=verbose,
                                    raw_page_responses=raw_page_responses)

    async def get_previous_close(self, ticker: str, adjusted: bool = True,
                                 raw_response: bool = False):
        """
        Get the previous day's open, high, low, and close (OHLC) for the specified option contract - Async
        `Official Docs <https://polygon.io/docs/options/get_v2_aggs_ticker__optionsticker__prev>`__

        :param ticker: The ticker symbol of the options contract. Eg: ``O:TSLA210903C00700000``
        :param adjusted: Whether or not the results are adjusted for splits. By default, results are adjusted.
                         Set this to false to get results that are NOT adjusted for splits.
        :param raw_response: Whether or not to return the ``Response`` Object. Useful for when you need to say
                             check the status code or inspect the headers. Defaults to False which returns the json
                             decoded dictionary.
        :return: Either a Dictionary or a Response object depending on value of ``raw_response``. Defaults to Dict.
        """

        _path = f'/v2/aggs/ticker/{ensure_prefix(ticker)}/prev'

        _data = {'adjusted': 'true' if adjusted else 'false'}

        _res = await self._get_response(_path, params=_data)

        if raw_response:
            return _res

        return json_lib.loads(_res.text)


# ========================================================= #


class OptionSymbol:
    """
    The custom object for parsed details from option symbols.
    """

    def __init__(self, option_symbol: str, expiry_format='date', symbol_format='polygon', fmt: str = 'underscore'):
        """
        Parses the details from symbol and creates attributes for the object.

        :param option_symbol: the symbol you want to parse. Both ``TSLA211015P125000`` and ``O:TSLA211015P125000`` are
                              valid
        :param expiry_format: The format for the expiry date in the results. Defaults to ``date`` object. change this
                              param to ``string`` to get the value as a string: ``YYYY-MM-DD``
        :param symbol_format: Which formatting spec to use. Defaults to polygon. also supports ``tda`` which is the
                              format supported by TD Ameritrade
        :param fmt: tda has two formats. one having an underscore in between (used by TDA API). and other starts with a
                    dot (``.``). Defaults to the underscore format. **If you're not sure, leave to default.** Pass
                    ``'dot'`` to get dot format. (ONLY use when using tda formats, has no effect on polygon format)
        """
        if symbol_format == 'polygon':
            if option_symbol.startswith('O:'):
                option_symbol = option_symbol[2:]

            self.underlying_symbol = option_symbol[:-15]

            _len = len(self.underlying_symbol)

            # optional filter for those Corrections Ian talked about
            self.underlying_symbol = ''.join([x for x in self.underlying_symbol if not x.isdigit()])

            self._expiry = option_symbol[_len:_len + 6]

            self.expiry = datetime.date(int(datetime.date.today().strftime('%Y')[:2] + self._expiry[:2]),
                                        int(self._expiry[2:4]), int(self._expiry[4:6]))

            self.call_or_put = option_symbol[_len + 6].upper()

            self.strike_price = int(option_symbol[_len + 7:]) / 1000

            self.option_symbol = f'{self.underlying_symbol}{option_symbol[_len:]}'

            if expiry_format in ['string', 'str', str]:
                self.expiry = self.expiry.strftime('%Y-%m-%d')

        elif symbol_format == 'tda':
            if fmt == 'dot':
                option_symbol, num = option_symbol[1:].upper(), 0

                for char in option_symbol:
                    if char.isalpha():
                        num += 1
                        continue
                    break

                option_symbol = f'{option_symbol[:num]}_{option_symbol[num+2:num+4]}{option_symbol[num+4:num+6]}' \
                                f'{option_symbol[num:num+2]}{option_symbol[num+6:]}'

            # Usual flow
            _split = option_symbol.split('_')

            self.underlying_symbol = _split[0]

            self._expiry = _split[1][:6]

            self.expiry = datetime.date(int(datetime.date.today().strftime('%Y')[:2] + self._expiry[4:6]),
                                        int(self._expiry[:2]), int(self._expiry[2:4]))

            self.call_or_put = _split[1][6]

            self.strike_price = int(float(_split[1][7:])) if float(_split[1][7:]) == int(float(_split[1][7:])) else \
                float(_split[1][7:])

            self.option_symbol = option_symbol

            if expiry_format in ['string', 'str', str]:
                self.expiry = self.expiry.strftime('%Y-%m-%d')

    def __repr__(self):
        return f'Underlying: {self.underlying_symbol} || expiry: {self.expiry} || type: {self.call_or_put} || ' \
               f'strike_price: {self.strike_price}'


def ensure_prefix(symbol: str):
    """
    Ensure that the option symbol has the prefix ``O:`` as needed by polygon endpoints. If it does, make no changes. If
    it doesn't, add the prefix and return the new value.

    :param symbol: the option symbol to check
    """
    if len(symbol) < 15:
        raise ValueError('Option symbol length must at least be 15 letters. See documentation on option symbols for '
                         'more info')

    if symbol.upper().startswith('O:'):
        return symbol.upper()

    return f'O:{symbol.upper()}'


# ========================================================= #


if __name__ == '__main__':  # Tests
    print('Don\'t You Dare Running Lib Files Directly')

# ========================================================= #
