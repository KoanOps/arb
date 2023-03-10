from src.model import Model
from data import tokens, settings
import threading

def checker(model, exchange, asset):
    change_f = model.estimate_arbitrage_forward(exchange, asset)
    change_b = model.estimate_arbitrage_backward(exchange, asset)
    model.log("{:5}: {:8.5f}% / {:8.5f}%".format(asset, change_f, change_b))
    if change_f > settings.MIN_DIFFERENCE:
        model.log("{:5} @{:.4f}".format(asset, change_f))
        model.run_arbitrage_forward(exchange, asset)
    elif change_b > settings.MIN_DIFFERENCE:
        model.log("{:5} @{:.4f}".format(asset, change_b))
        model.run_arbitrage_backward(exchange, asset)

def run(model, exchange, n_threads):
    alts = tokens.binance_tokens
    while True:
        for i in range(0, len(alts), n_threads):
            alts_batch = alts[i:i + n_threads]
            threads = []
            for asset in alts_batch:
                threads.append(threading.Thread(target=checker, args=(model, exchange, asset)))
                threads[-1].start()
            for thread in threads:
                thread.join()
            model.reset_cache()

if __name__ == "__main__":
    model = Model()
    exchange = model.binance
    n_threads = 5
    run(model, exchange, n_threads)