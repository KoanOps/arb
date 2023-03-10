from datetime import datetime
from operator import itemgetter
from data import secrets, settings
import time
import ccxt
class Model:
    binance = None
    fee = 0.999
    cache_prices = []
    cache_order_books = []
    not_filled = 0
    in_progress = 1
    filled = 2
    def __init__(self):
        self.binance = ccxt.binance({
            'apiKey': secrets.BINANCE_KEY, 'secret': secrets.BINANCE_SECRET, 'timeout': 30000,
            'enableRateLimit': True
        })
    def buy(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None, timeout=None):
        try:
            if amount_percentage:
                asset2_available = self.get_balance(exchange, asset2) * amount_percentage
                amount = asset2_available / self.get_price(exchange, asset1, asset2, mode='ask')
            self.log("Buying {:.6} {} with {} on {}.".format(
                amount, asset1, asset2, exchange
            ))
            if limit:
                self.log("Limit {}.".format(limit))
            if not limit:
                self.log("Market")
                exchange.createMarketBuyOrder(
                    '{}/{}'.format(asset1, asset2), amount
                )
                return True
            else:
                exchange.createLimitBuyOrder(
                    '{}/{}'.format(asset1, asset2), amount, limit
                )
                if timeout:
                    time.sleep(timeout)
                    result = self.is_open_order(exchange, asset1, asset2)
                    if result == Model.not_filled:
                        if self.cancel_orders(exchange, asset1, asset2):
                            self.log("Canceled limit {}/{}.".format(asset1, asset2))
                        return False
                    elif result == Model.in_progress:
                        n = 0
                        while result == Model.in_progress:
                            n += 1
                            if n >= 20:
                                self.log("Selling {} to {}.".format(asset1, asset2))
                                self.sell(exchange, asset1, asset2, amount_percentage=1)
                                return False
                            self.log("Order {}/{} IP".format(asset1, asset2))
                            time.sleep(timeout)
                            result = self.is_open_order(exchange, asset1, asset2)
                        self.log("Limit exec")
                        return True
                    else:
                        self.log("Limit exec")
                        return True
                else:
                    return False
        except Exception as e:
            self.log("Error {}".format(str(e)))
            return False
    def sell(self, exchange, asset1, asset2, amount_percentage=None, amount=None, limit=None, timeout=None):
        try:
            if amount_percentage:
                amount = self.get_balance(exchange, asset1) * amount_percentage
            self.log("Sell {:.6f} {} to {} on {}.".format(
                amount, asset1, asset2, exchange
            ))

            if limit:
                self.log("Limit {}.".format(limit))

            if not limit:
                self.log("Market")
                exchange.createMarketSellOrder(
                    '{}/{}'.format(asset1, asset2), amount
                )
                return True
            else:
                exchange.createLimitSellOrder(
                    '{}/{}'.format(asset1, asset2), amount, limit
                )
                if timeout:
                    time.sleep(timeout)
                    result = self.is_open_order(exchange, asset1, asset2)

                    if result == Model.not_filled:
                        if self.cancel_orders(exchange, asset1, asset2):
                            self.log("Canceled limit {}/{}".format(asset1, asset2))
                        return False
                    elif result == Model.in_progress:
                        n = 0
                        while result == Model.in_progress:
                            n += 1
                            if n >= 20:
                                self.log("Buying {} with {}.".format(asset1, asset2))
                                self.buy(exchange, asset1, asset2, amount_percentage=1)
                                return False

                            self.log("Order {}/{} IP".format(asset1, asset2))
                            time.sleep(timeout)
                            result = self.is_open_order(exchange, asset1, asset2)

                        self.log("Limit")
                        return True
                    else:
                        self.log("Limit")
                        return True
                else:
                    return False
        except Exception as e:
            self.log("Error: {}".format(str(e)))
            return False
    def reset_cache(self):
        self.cache_prices = []
        self.cache_order_books = []
    def get_price_cache(self, exchange, asset1, asset2):
        for item in self.cache_prices:
            if item['asset1'] == asset1 and item['asset2'] == asset2 and item['exchange'] == str(exchange):
                return item['ticker']
        return None
    def get_order_book_cache(self, exchange, asset1, asset2):
        for item in self.cache_order_books:
            if item['asset1'] == asset1 and item['asset2'] == asset2 and item['exchange'] == str(exchange):
                return item['book']
        return None
    def cache_add_price(self, exchange, asset1, asset2, ticker):
        self.cache_prices.append({
            'exchange': str(exchange), 'asset1': asset1, 'asset2': asset2, 'ticker': ticker
        })
    def cache_order_book(self , exchange, asset1, asset2, book):
        self.cache_order_books.append({
            'exchange': str(exchange), 'asset1': asset1, 'asset2': asset2, 'book': book
        })
    def get_balance(self, exchange, asset):
        try:
            balance = exchange.fetchBalance()
            if asset in balance:
                return balance[asset]['free']
            return 0
        except Exception as e:
            self.log("Error {}".format(str(e)))
            raise
    def get_price(self, exchange, asset1, asset2, mode='average'):
        try:
            if self.get_price_cache(exchange, asset1, asset2):
                ticker = self.get_price_cache(exchange, asset1, asset2)
            else:
                ticker = exchange.fetchTicker('{}/{}'.format(asset1, asset2))
                self.cache_add_price(exchange, asset1, asset2, ticker)
            if mode == 'bid':
                return ticker['bid']
            if mode == 'ask':
                return ticker['ask']
            return (ticker['ask'] + ticker['bid']) / 2
        except Exception as e:
            self.log("Error {}/{}: {}".format(asset1, asset2, str(e)))
            return None
    def get_order_book(self, exchange, asset1, asset2, mode="bids"):
        try:
            order_book = self.get_order_book_cache(exchange, asset1, asset2)
            if not order_book:
                order_book = exchange.fetchOrderBook('{}/{}'.format(asset1, asset2))
                self.cache_order_book(exchange, asset1, asset2, order_book)

            return order_book[mode]
        except Exception as e:
            self.log("Error {}/{}: {}".format(asset1, asset2, str(e)))
            return None
    def get_buy_limit_price(self, exchange, asset1, asset2, amount=1):
        bids = self.get_order_book(exchange, asset1, asset2, mode="asks")
        if not bids:
            return None
        bids.sort()
        if len(bids) < settings.ESTIMATION_ORDERBOOK:
            return None
        for bid in bids[settings.ESTIMATION_ORDERBOOK:]:
            if bid[1] >= amount:
                return bid[0]
    def get_sell_limit_price(self, exchange, asset1, asset2, amount=1):
        asks = self.get_order_book(exchange, asset1, asset2, mode="bids")
        if not asks:
            return None
        asks.sort(reverse=True)
        if len(asks) < settings.ESTIMATION_ORDERBOOK:
            return None
        for ask in asks[settings.ESTIMATION_ORDERBOOK:]:
            if ask[1] >= amount:
                return ask[0]
    def is_open_order(self, exchange, asset1, asset2):
        try:
            data = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
            for item in data:
                if item['filled'] > 0:
                    return Model.in_progress
            if len(data) > 0:
                return Model.not_filled
            return Model.filled
        except Exception as e:
            self.log("Error {}/{}: {}".format(asset1, asset2, str(e)))
            return None
    def cancel_orders(self, exchange, asset1, asset2):
        for _ in range(5):
            try:
                orders = exchange.fetchOpenOrders('{}/{}'.format(asset1, asset2))
                for order in orders:
                    exchange.cancelOrder(order['id'], '{}/{}'.format(asset1, asset2))
                return True
            except Exception as e:
                self.log("Error {}/{}: {}.".format(asset1, asset2, str(e)))

        self.log("Unable {}/{}.".format(asset1, asset2, str(e)))
        return

    def estimate_arbitrage_forward(self, exchange, asset):
        try:
            alt_eth = self.get_buy_limit_price(exchange, asset, 'ETH')
            alt_btc = self.get_sell_limit_price(exchange, asset, 'BTC')

            if not alt_btc or not alt_eth:
                self.log("Skipping.".format(asset, str(exchange)))
                return -100

            step_1 = (1 / alt_eth) * self.fee
            step_2 = (step_1 * alt_btc) * self.fee
            step_3 = (step_2 / self.get_price(exchange, 'ETH', 'BTC', mode='ask')) * self.fee

            return (step_3 - 1) * 100
        except ZeroDivisionError:
            return -1
    def estimate_arbitrage_backward(self, exchange, asset):
        try:
            alt_btc = self.get_buy_limit_price(exchange, asset, 'BTC')
            alt_eth = self.get_sell_limit_price(exchange, asset, 'ETH')
            if not alt_btc or not alt_eth:
                self.log("Skipping {} on {}, .".format(asset, str(exchange)))
                return -100
            step_1 = (self.get_price(exchange, 'ETH', 'BTC', mode='bid')) * self.fee
            step_2 = (step_1 / alt_btc) * self.fee
            step_3 = (step_2 * alt_eth) * self.fee
            return (step_3 - 1) * 100
        except ZeroDivisionError:
            return -1
    def run_arbitrage_forward(self, exchange, asset):
        self.log("Arb on {}: ETH {} BTC ETH".format(exchange, asset))
        balance_before = self.get_balance(exchange, "ETH")
        result1 = self.best_buy(exchange, asset, 'ETH', 1)
        if not result1:
            self.log("Failed {} to ETH, cancel.".format(asset))
            return
        result2 = self.best_sell(exchange, asset, 'BTC', 1)
        if not result2:
            self.log(
                "Failed {} to BTC {} to ETH.".format(asset, asset))
            self.sell(exchange, asset, 'ETH', amount_percentage=1)
            self.summarize_arbitrage(exchange, balance_before, asset)
            return
        self.buy(exchange, "ETH", "BTC", amount_percentage=1)
        self.summarize_arbitrage(exchange, balance_before, asset)
    def run_arbitrage_backward(self, exchange, asset):
        self.log("Arbitrage on {}: ETH -> BTC -> {} -> ETH".format(exchange, asset))
        balance_before = self.get_balance(exchange, "ETH")
        self.sell(exchange , "ETH", "BTC", 1)
        result1 = self.best_buy(exchange, asset, 'BTC', 1)
        if not result1:
            self.log("Failed BTC to {}, cancel".format(asset))
            self.buy(exchange, 'ETH', 'BTC', amount_percentage=1)
            self.summarize_arbitrage(exchange, balance_before, asset)
            return
        result2 = self.best_sell(exchange, asset, 'ETH', 1)
        if not result2:
            self.log(
                "Failed {} to ETH, cancel {} to ETH.".format(asset,  asset))
            self.sell(exchange, asset, 'ETH', amount_percentage=1)
            self.summarize_arbitrage(exchange, balance_before, asset)
            return
        self.summarize_arbitrage(exchange, balance_before, asset)
    @staticmethod
    def log(text):
        formatted_text = "[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), text)
        with open('self.logs.txt', 'a+') as file:
            file.write(formatted_text)
            file.write("\n")
    def best_buy(self, exchange, asset1, asset2, amount_percentage):
        order_book = self.get_order_book(exchange, asset1, asset2, mode="asks")
        order_book.sort(key=itemgetter(0))
        for price in order_book[:settings.MAX_TRIES_ORDERBOOK]:
            self.log("Trying to buy {} with {} @{:.8f}.".format(asset1, asset2, price[0]))
            result = self.buy(exchange, asset1, asset2, amount_percentage=amount_percentage, limit=price[0],
                              timeout=settings.WAIT_BETWEEN_ORDER)
            if result:
                self.log("Bought {} with {} {:.8f}.".format(asset1, asset2, price[0]))
                return True
            else:
                self.log("Failed {} with {} at {:.8f}.".format(asset1, asset2, price[0]))

        self.log("No {} with {}".format(asset1, asset2))
        return False
    def best_sell(self, exchange, asset1, asset2, amount_percentage):
        order_book = self.get_order_book(exchange, asset1, asset2, mode="bids")
        order_book.sort(key=itemgetter(0), reverse=True)
        for price in order_book[:settings.MAX_TRIES_ORDERBOOK]:
            self.log("Trying {} to {} @{:.8f}.".format(asset1, asset2, price[0]))
            result = self.sell(exchange, asset1, asset2, amount_percentage=amount_percentage, limit=price[0],
                               timeout=settings.WAIT_BETWEEN_ORDER)
            if result:
                self.log("Sold {} to {} {:.8f}.".format(asset1, asset2, price[0]))
                return True
            else:
                self.log("Failed {} to {} at {:.8f}.".format(asset1, asset2, price[0]))

        self.log("No {} to {}".format(asset1, asset2))
        return False
    def summarize_arbitrage(self, exchange, balance_before, asset):
        balance_after = self.get_balance(exchange, "ETH")
        diff = balance_after - balance_before
        diff_usd = diff * self.get_price(exchange, 'ETH', 'USD')
        self.log("Arb {:5}, diff: {:8.6f}ETH ({:.2f} USD).".format(asset, diff, diff_usd))