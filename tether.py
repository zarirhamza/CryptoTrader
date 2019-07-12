import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from logbook import Logger
from catalyst import run_algorithm
from catalyst.api import (order, order_target_value, symbol, record,
                          cancel_order, get_open_orders, order_target_percent)
from catalyst.exchange.utils.stats_utils import extract_transactions

NAMESPACE = 'Tether'
log = Logger(NAMESPACE)

def initialize(context):
    context.ASSET_NAME = 'usdc_usdt'
    context.asset = symbol(context.ASSET_NAME)
    context.i = 0;
    context.state = "sold";
    context.boughtPrice = 1;

def handle_data(context, data):
    context.i += 1
    # context.i % 1 == 0
    cash = context.portfolio.cash
    # Retrieve current asset price from pricing data
    price = data.current(context.asset, 'price')

    record(
        price=price,
        volume=data.current(context.asset, 'volume'),
        cash=cash,
        starting_cash=context.portfolio.starting_cash,
    )
    #if(context.i % 60 == 0):
    '''
    Highs = data.history(context.asset,
                         'high',
                         bar_count=30,
                         frequency="1M",
                         )

    Lows = data.history(context.asset,
                        'low',
                        bar_count=30,
                        frequency="1M",
                        )

    Closes = data.history(context.asset,
                          'close',
                          bar_count=30,
                          frequency="1M",
                          )

    Prices = data.history(context.asset,
                          'price',
                          bar_count=30,
                          frequency="1M",
                          )

    ATR = Highs[0] - Lows[0]
    for i in range(1, 29):
        ATR = ATR + max((Highs[i] - Lows[i]), abs(Highs[i] - Closes[i - 1]), abs(Lows[i] - Closes[i - 1]))
    ATR = ATR / 29
    '''

    if(price > 1.01 and context.state == "bought"):
        order_target_percent(context.asset, 0);
        context.state = "sold";
    elif (price <= 1.01 and context.state == "sold"):
        order(context.asset, 1);
        context.state = "bought";
        context.boughtPrice = price;



def analyze(context, perf):
    # Get the quote_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    quote_currency = exchange.quote_currency.upper()

    # First chart: Plot portfolio value using quote_currency
    ax1 = plt.subplot(211)
    perf.loc[:, ['portfolio_value']].plot(ax=ax1)
    ax1.legend_.remove()
    ax1.set_ylabel('Portfolio Value\n({})'.format(quote_currency))
    start, end = ax1.get_ylim()
    ax1.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

    # Second chart: Plot asset price, moving averages and buys/sells
    ax2 = plt.subplot(212, sharex=ax1)
    perf.loc[:, ['price', 'short_mavg', 'long_mavg']].plot(
        ax=ax2,
        label='Price')
    ax2.legend_.remove()
    ax2.set_ylabel('{asset}\n({quote})'.format(
        asset=context.asset.symbol,
        quote=quote_currency
    ))
    start, end = ax2.get_ylim()
    ax2.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

    transaction_df = extract_transactions(perf)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df['amount'] > 0]
        sell_df = transaction_df[transaction_df['amount'] < 0]
        ax2.scatter(
            buy_df.index.to_pydatetime(),
            perf.loc[buy_df.index, 'price'],
            marker='^',
            s=100,
            c='green',
            label=''
        )
        ax2.scatter(
            sell_df.index.to_pydatetime(),
            perf.loc[sell_df.index, 'price'],
            marker='v',
            s=100,
            c='red',
            label=''
        )
    plt.show()

if __name__ == '__main__':
    run_algorithm(
        capital_base=1000,
        data_frequency='minute',
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name='binance',
        algo_namespace=NAMESPACE,
        quote_currency='usdc',
        start=pd.to_datetime('2019-06-01', utc=True),
        end=pd.to_datetime('2019-06-30', utc=True),
    )