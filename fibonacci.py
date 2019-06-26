import pandas as pd
import matplotlib.pyplot as plt

from catalyst import run_algorithm
from catalyst.api import (order, order_target_value, symbol, record,
                          cancel_order, get_open_orders, order_target_percent)

def initialize(context):
    context.ASSET_NAME = 'ltc_usdt'
    context.asset = symbol(context.ASSET_NAME)
    context.i = -1

    context.TARGET_HODL_RATIO = 0.8

    context.startParabola=0 #begin parabolic movement
    context.endParabola=0 #end parabolic movement
    context.trackingState = 0 #0=nonparabolic ,
                              # 1=beginning movment
                              # 2 = dropping off,
                              # 3 = rising up again
                              # 4 = fibonacci and sell


def handle_data(context, data):
    context.i += 1
    #context.i % 1 == 0
    if(1):
        cash = context.portfolio.cash
        # Retrieve current asset price from pricing data
        price = data.current(context.asset, 'price')

        record(
            price=price,
            volume=data.current(context.asset, 'volume'),
            cash=cash,
            starting_cash=context.portfolio.starting_cash,
        )


        if(context.trackingState != 0):
            print(str(context.i) + " times ran")
            print(str(context.trackingState) + " current state")
            print(str(cash) + " - current cash")
            print(str(context.startParabola) + " " + str(context.endParabola))

        if context.trackingState == 0: #FIND PARABOLA
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
            for i in range(1,14):
                ATR = ATR + max ((Highs[i] - Lows[i]),abs(Highs[i] - Closes[i-1]), abs(Lows[i]-Closes[i-1]))
            ATR = ATR/14
            #print(str(ATR) + " - ATR")
            #print(str(Prices[13]) + " - start P")
            #print(str(Prices[14]) + " - end P")

            if (Prices[14] > Prices[13] + (3 * ATR)):
                context.trackingState = 1
                context.startParabola = Prices[13]
                context.endParabola = Prices[14]
            else:
                return

        #DO WE NEED CONFIRMATION OF ENDING OF PARABOLA?

        elif context.trackingState == 1: # tracking for dipping below 50 percent
            Prices = data.history(context.asset,
                                  'price',
                                  bar_count=2,
                                  frequency= "1M",
                                  )
            #Prices[1] is current value and Prices[0] is previous value

            #print(str(Prices[1]) + " " + str(0.5 * (context.endParabola - context.startParabola)) + " " + str(
            #   0.22 * (context.endParabola - context.startParabola)) + " " + str(
            #    0.75 * (context.endParabola - context.startParabola)))

            if (context.endParabola - Prices[1]) > 0.68 * (context.endParabola - context.startParabola):
                context.trackingState = 2
            elif (Prices[1]) > 1.1 * (context.endParabola): #rewrite this later
                context.trackingState = 0 # reset parabola its too far up
            else:
                return

        elif context.trackingState == 2: #buying once above fifty percent again
            Prices = data.history(context.asset,
                                  'price',
                                  bar_count=2,
                                  frequency="1M",
                                  )

            #print(str(Prices[1]) + " " + str(0.5 * (context.endParabola - context.startParabola)) + " " + str(
            #    0.22 * (context.endParabola - context.startParabola)) + " " + str(
            #    0.75 * (context.endParabola - context.startParabola)))

            if (context.endParabola - Prices[1]) < 0.68 * (context.endParabola - context.startParabola):
                order_target_percent(context.asset, 1) #arbitrary now
                print('buying')
                context.trackingState = 3
            #BELOW IS STOPGAP REPEATED ALWAYS
            elif (context.endParabola - Prices[1]) > 0.75 * (context.endParabola - context.startParabola):
                order_target_percent(context.asset, 0)
                # context.trackingState = 0
                # if value drops too much reset - STOPGAP
            else:
                return

        elif context.trackingState >= 3:
            Prices = data.history(context.asset,
                                  'price',
                                  bar_count=2,
                                  frequency="1M",)
            #print(str(Prices[1]) + " " + str(0.5 * (context.endParabola - context.startParabola)) + " " + str(0.22 * (context.endParabola - context.startParabola)) + " " + str(0.75 * (context.endParabola - context.startParabola)))
            if (context.endParabola - Prices[1]) < 0.22 * (context.endParabola - context.startParabola):
                context.trackingState = context.trackingState + 1
                if (context.trackingState == 6): #check 3 times
                    order_target_percent(context.asset, 0)
                    context.trackingState = 0
                    # BELOW IS STOPGAP REPEATED ALWAYS
            elif (context.endParabola - Prices[1]) > 0.75 * (context.endParabola - context.startParabola):
                    order_target_percent(context.asset, 0)
                    context.trackingState = 0
                    # if value drops too much reset - STOPGAP
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
        capital_base=10000,
        data_frequency='minute',
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        exchange_name='bitfinex',
        algo_namespace='buy_and_hodl',
        quote_currency='usdt',
        start=pd.to_datetime('2019-05-03', utc=True),
        end=pd.to_datetime('2019-05-04', utc=True),
    )