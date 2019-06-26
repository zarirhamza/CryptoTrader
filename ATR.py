import pandas as pd
import matplotlib.pyplot as plt

from catalyst import run_algorithm
from catalyst.api import (order, order_target_value, symbol, record,
                          cancel_order, get_open_orders, order_target_percent)

def initialize(context):
    context.ASSET_NAME = 'ltc_usdt'
    context.asset = symbol(context.ASSET_NAME)
    context.i = -1
    context.ATR = 1


def handle_data(context, data):
    if(context.i == -1):
        order_target_percent(context.asset, 1)
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
    if (context.i % 60 == 0):
        Highs = data.history(context.asset,
                             'high',
                             bar_count=15,
                             frequency="1M",
                             )

        Lows = data.history(context.asset,
                            'low',
                            bar_count=15,
                            frequency="1M",
                            )

        Closes = data.history(context.asset,
                              'close',
                              bar_count=15,
                              frequency="1M",
                              )

        Prices = data.history(context.asset,
                              'price',
                              bar_count=15,
                              frequency="1M",
                              )

        ATR = Highs[0] - Lows[0]
        for i in range(1, 14):
            ATR = ATR + max((Highs[i] - Lows[i]), abs(Highs[i] - Closes[i - 1]), abs(Lows[i] - Closes[i - 1]))
        ATR = ATR / 14
        # print(str(ATR) + " - ATR")
        # print(str(Prices[13]) + " - start P")
        # print(str(Prices[14]) + " - end P")
        print(str(Prices[14]) + " -current price")
        print(str(ATR) + " - ATR")
        print(str(Prices[13]) + " -previous price")
        print (str(cash) + " -current cash")
        if (Prices[14] > Prices[13] + (3 * ATR) and context.ATR == 0):
            order_target_percent(context.asset, 0)
            context.ATR = ATR
        elif (Prices[14] > Prices[13] + (1.5 * ATR) and context.ATR != 0):
            order_target_percent(context.asset, 1)
            context.ATR = 0
        elif (Prices[14] < Prices[13] + (1.5 * ATR) and context.ATR != 0):
            order_target_percent(context.asset, 1)
            context.ATR = 0
        else:
            return


def analyze(context=None, results=None):
    # Plot the portfolio and asset data.
    ax1 = plt.subplot(211)
    results[['portfolio_value']].plot(ax=ax1)
    ax1.set_ylabel('Portfolio\nValue\n(USD)')

    ax2 = plt.subplot(212, sharex=ax1)
    ax2.set_ylabel('{asset}\n(USD)'.format(asset=context.ASSET_NAME))
    results[['price']].plot(ax=ax2)

    trans = results.ix[[t != [] for t in results.transactions]]
    buys = trans.ix[
        [t[0]['amount'] > 0 for t in trans.transactions]
    ]
    ax2.scatter(
        buys.index.to_pydatetime(),
        results.price[buys.index],
        marker='^',
        s=100,
        c='g',
        label=''
    )

    # Show the plot.
    plt.gcf().set_size_inches(18, 8)
    plt.show()

if __name__ == '__main__':
    run_algorithm(
        capital_base=1000,
        data_frequency='minute',
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name='bitfinex',
        algo_namespace='buy_and_hodl',
        quote_currency='usdt',
        start=pd.to_datetime('2018-05-25', utc=True),
        end=pd.to_datetime('2018-06-04', utc=True),
    )