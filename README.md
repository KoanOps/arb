<h1>Arbitrage Bot</h1>

<p>This is a work sample of Cryptoexchange, Inc's older trading bot that allowed the company to take advantage of price differences via arbitrage on Binance, written in Python using the ccxt library.</p>

<p>It runs in an infinite loop, continuously checking for arbitrage opportunities. 
When opportunities are found, the bot executes trades to take advantage of them.
The bot uses multiple threads to scan opportunities in parallel, and logs its activity to a file.</p>

<h2>Prerequisites</h2>

<ul>
<li>Python 3</li>
<li>A Binance account and API key</li>
<li>CCXT, a library for trading cryptocurrencies with support for a wide range of markets and merchant APIs</li>
</ul>

<h2>Configuration</h2>
<p>The API/Secret keys can be changed in the <code>data/secrets.py</code> file. Do not disclose your API Key, Secret Key (HMAC), or Private Key (RSA) to anyone to avoid asset losses. You should treat them like your passwords.</p>

<ul>
      <li><code>BINANCE_KEY</code>: Your Binance API key.</li>
      <li><code>BINANCE_SECRET</code>: Your Binance secret key.</li>
</ul>

<p>The bot's behavior can be customized by modifying the values in the <code>data/settings.py</code> file. Here are some of the key settings you may want to adjust:</p>

<ul>
      <li><code>MIN_DIFFERENCE</code>: The minimum price difference (in percentage) required to trigger an arbitrage trade.</li>
      <li><code>MAX_TRADE_AMOUNT</code>: The maximum amount (in USD) that can be traded in a single arbitrage trade.</li>
      <li><code>MAX_SLIPPAGE</code>: The maximum slippage (in percentage) allowed for executing an arbitrage trade.</li>
      <li><code>REFRESH_INTERVAL</code>: The interval (in seconds) at which the bot refreshes its data and looks for new arbitrage opportunities.</li>
</ul>

<h2>Usage</h2>
<p>You can install the required package using <code>pip</code>:</p>

<pre><code>pip install ccxt</code></pre>

<p>To use the bot, simply run the <code>ini.py</code> script:</p>

<pre><code>python ini.py</code></pre>

<p>The bot will then start monitoring the supported tokens and exchanges for price differences, and execute arbitrage trades when profitable opportunities arise.</p>

<h2>Disclaimer</h2>
<p>This bot is intended only for work reference. It should not be used for actual trading purposes without extensive testing and modification. 
The user should fully understand the risks involved with automated trading and arbitrage, as well as any potential issues that may arise from using this code leading to potential losses. 
The author is not liable for any losses.</p>
