# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from abupy import AbuFactorSellOptionHedgeMin

from abupy import AbuFactorBuyBreak, AbuFactorBuyMA, AbuTwoDayBuy, AbuFactorBuyEuroOptionHedge, AbuFactorSellEuroOptionHedge, AbuFactorSellClosePosition
from abupy import AbuFactorSellBreakMACloseCallPosition, AbuFactorSellBreakMAClosePutPosition, AbuFactorBuyPutBreakSellOption1M, AbuFactorBuyBreakSellOption1M
from abupy import abu, ABuDateUtil, ABuMySQLUtil
from abupy import env
from abupy.MarketBu.ABuMarket import all_symbol
from abupy.BetaBu import ABuPtPosition, AbuAtrPosition, AbuClosePosition, AbuEuroOptionHedgeBuyPosition, AbuEuroOptionHedgeSellPosition

from abupy import AbuFactorBuyPutBreakSellOption, AbuFactorSellClearPut, AbuFactorSellClearCall, AbuFactorSellOptionHedge, AbuFactorBuyBreakSellOption, AbuFactorSellClearStraddle
from abupy import AbuFactorSellBreakLowCloseCall, AbuFactorSellBreakHighClosePut, AbuFactorBuyPutOptionEachDay, AbuFactorBuyOptionEachDay
from abupy import AbuSlippageBuyPutTick, AbuSlippageSellPutTick, AbuFactorSellExceedDailyRatioClosePut, AbuFactorSellExceedDailyRatioCloseCall
from abupy import store_abu_result_out_put_and_plot

if __name__ == '__main__':
    env.g_dominant_contract = True
    env.g_high_freq_data = True
    env.g_capital_hf = False
    # us_choice_symbols = all_symbol()
    # us_choice_symbols.remove('WR0')
    # us_choice_symbols.remove('BB0')
    # us_choice_symbols.remove('WH0')
    # us_choice_symbols.remove('SF0')
    us_choice_symbols = ['ZC', 'M', 'MA', 'J', 'JM', 'AP', 'RB', 'CU', 'JD', 'I', 'CF']
    # us_choice_symbols = ['J']

    sell_factors = []

    break_xd_lis = list(range(5, 6))
    clear_xd_lis = list(range(4, 5))
    option_max_num_lis = list(range(10, 11))
    # maturity_lis = list(range(10, 23))
    option_clear_proportion_lis = [0.5, ]
    dynamic_lis = [False]

    for clear_xd in clear_xd_lis:
        for option_max_num in option_max_num_lis:
            for option_clear_proportion in option_clear_proportion_lis:
                for dynamic in dynamic_lis:
                    for break_xd in break_xd_lis:
                        buy_factors = [
                            # {'class': AbuFactorBuyOptionEachDay, 'freq': '60m', 'xd': 8, 'xd1': 16, 'cp': -1, 'direction': -1, 'maturity': 3,
                            #  'premium': 20000, 'threshold': 0.3, 'notional': None,
                            #  'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                            #  'sell_factors': [{'class': AbuFactorSellOptionHedge,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.3},
                            #                   {'class': AbuFactorSellClearStraddle,
                            #                    'position': AbuEuroOptionHedgeSellPosition}
                            #                   ]},
                            #
                            # {'class': AbuFactorBuyPutOptionEachDay, 'freq': '60m', 'xd': 8, 'xd1': 16, 'cp': 1, 'direction': -1, 'maturity': 3,
                            #  'premium': 20000, 'threshold': 0.3, 'notional': None, 'slippage': AbuSlippageBuyPutTick,
                            #  'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                            #  'sell_factors': [{'class': AbuFactorSellOptionHedge,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.3,
                            #                    'slippage': AbuSlippageSellPutTick},
                            #                   {'class': AbuFactorSellClearStraddle,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'slippage': AbuSlippageSellPutTick}
                            #                   ]}

                            {'class': AbuFactorBuyBreakSellOption, 'freq': '1d', 'xd': break_xd, 'xd1': clear_xd, 'cp': 1, 'direction': 1,
                             'maturity': 22, 'dynamic': dynamic,
                             'premium': 100000, 'threshold': 0.2, 'notional': None, 'option_max_num': option_max_num, 'option_clear_proportion': option_clear_proportion,
                             'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                             'sell_factors': [{'class': AbuFactorSellOptionHedge,
                                               'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.2},
                                              {'class': AbuFactorSellClearCall,
                                               'position': AbuEuroOptionHedgeSellPosition},

                                              ]},

                            {'class': AbuFactorBuyPutBreakSellOption, 'freq': '1d', 'xd': break_xd, 'xd1': clear_xd, 'cp': -1, 'direction': 1,
                             'maturity': 22, 'option_max_num': option_max_num, 'option_clear_proportion': option_clear_proportion, 'dynamic': dynamic,
                             'premium': 100000, 'threshold': 0.2, 'notional': None, 'slippage': AbuSlippageBuyPutTick,
                             'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                             'sell_factors': [{'class': AbuFactorSellOptionHedge,
                                               'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.2,
                                               'slippage': AbuSlippageSellPutTick},
                                              {'class': AbuFactorSellClearPut,
                                               'position': AbuEuroOptionHedgeSellPosition, 'slippage': AbuSlippageSellPutTick},

                                              ]},

                            # {'class': AbuFactorBuyBreakSellOption, 'freq': '60m', 'xd': 8, 'xd1': 12, 'cp': -1, 'direction': -1,
                            #  'maturity': 5, 'dynamic': True,
                            #  'premium': 5000, 'threshold': 0.3, 'notional': None, 'option_max_num': 10, 'option_clear_proportion': 0.618,
                            #  'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                            #  'sell_factors': [{'class': AbuFactorSellOptionHedge,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.3},
                            #                   {'class': AbuFactorSellClearCall,
                            #                    'position': AbuEuroOptionHedgeSellPosition}
                            #                   ]},
                            #
                            # {'class': AbuFactorBuyPutBreakSellOption, 'freq': '60m', 'xd': 8, 'xd1': 12, 'cp': 1, 'direction': -1,
                            #  'maturity': 5, 'option_max_num': 10, 'option_clear_proportion': 0.618, 'dynamic': True,
                            #  'premium': 5000, 'threshold': 0.3, 'notional': None, 'slippage': AbuSlippageBuyPutTick,
                            #  'calendar_type': 1, 'rate': 0.03, 'dividend': 0.03, 'position': {'class': AbuEuroOptionHedgeBuyPosition},
                            #  'sell_factors': [{'class': AbuFactorSellOptionHedge,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'threshold': 0.3,
                            #                    'slippage': AbuSlippageSellPutTick},
                            #                   {'class': AbuFactorSellClearPut,
                            #                    'position': AbuEuroOptionHedgeSellPosition, 'slippage': AbuSlippageSellPutTick}
                            #                   ]}
                        ]

                        abu_result_tuple, kl_pd_manager = abu.run_loop_back(read_cash=20000000, buy_factors=buy_factors,
                                                                            sell_factors=sell_factors,
                                                                            choice_symbols=us_choice_symbols,
                                                                            start='2015-01-08',
                                                                            end='2017-11-30')

                        store_abu_result_out_put_and_plot(abu_result_tuple, show_log=True)

            # import cProfile
            #
            # cProfile.run("""abu_result_tuple, kl_pd_manager = abu.run_loop_back(read_cash=30000000, buy_factors=buy_factors,
            #                                                     sell_factors=sell_factors,
            #                                                     choice_symbols=us_choice_symbols,
            #                                                     start='2017-01-08',
            #                                                     end='2018-11-30')""")




