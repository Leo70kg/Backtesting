# -*- encoding:utf-8 -*-
"""期货度量模块"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import seaborn as sns

from ..CoreBu import ABuEnv
from ..UtilBu import ABuDateUtil
from ..MarketBu.ABuSymbolFutures import AbuFuturesCn
from ..ExtBu.empyrical import stats
from ..MetricsBu.ABuMetricsBase import AbuMetricsBase, valid_check
from ..UtilBu.ABuDTUtil import warnings_filter

__author__ = '阿布'
__weixin__ = 'abu_quant'


class AbuMetricsFutures(AbuMetricsBase):
    """期货度量类，主要区别在于不涉及benchmark"""

    def _metrics_base_stats(self):
        """度量真实成交了的capital_pd，即涉及资金的度量，期货相关不涉及benchmark"""
        # 资金利用率序列
        self.cash_utilization_series = 1 - (self.capital.capital_pd.cash_blance /
                                            self.capital.capital_pd.capital_blance)

        # 平均资金利用率
        self.cash_utilization = 1 - (self.capital.capital_pd.cash_blance /
                                     self.capital.capital_pd.capital_blance).mean()
        # 最大资金利用率
        self.cash_max_utilization = 1 - (self.capital.capital_pd.cash_blance /
                                         self.capital.capital_pd.capital_blance).min()

        self.algorithm_returns = np.round(self.capital.capital_pd['capital_blance'].pct_change(), 6)

        # 收益cum数据
        # noinspection PyTypeChecker
        self.algorithm_cum_returns = stats.cum_returns(self.algorithm_returns)

        # 最后一日的cum return
        self.algorithm_period_returns = self.algorithm_cum_returns[-1]

        # 回测起始日期
        self.start_date = ABuDateUtil.datetime_to_str(self.capital.capital_pd.index[0])

        # 回测结束日期
        self.end_date = ABuDateUtil.datetime_to_str(self.capital.capital_pd.index[-1])

        # 交易分钟数
        num = len(self.algorithm_cum_returns)
        # 交易天数
        self.num_trading_days = len(self.capital.capital_pd)
        # self.num_trading_days = round(num / 545) if ABuEnv.g_capital_hf else num

        # 年化收益
        self.algorithm_annualized_returns = \
            (ABuEnv.g_market_trade_year / self.num_trading_days) * self.algorithm_period_returns

        # noinspection PyUnresolvedReferences

        self.mean_algorithm_returns = self.algorithm_returns.cumsum() / np.arange(1, num + 1, dtype=np.float64) \
            if ABuEnv.g_capital_hf else self.algorithm_returns.cumsum() / np.arange(1, self.num_trading_days + 1,
                                                                                    dtype=np.float64)
        # noinspection PyTypeChecker
        self.algorithm_volatility = stats.annual_volatility(self.algorithm_returns)
        # noinspection PyTypeChecker
        self.algorithm_sharpe = stats.sharpe_ratio(self.algorithm_returns)
        # 最大回撤
        # noinspection PyUnresolvedReferences
        self.max_drawdown = stats.max_drawdown(self.algorithm_returns.values)

    @valid_check
    @warnings_filter  # skip: statsmodels / nonparametric / kdetools.py:20
    def plot_returns_cmp(self, only_show_returns=False, only_info=False, save_plot_path=None, save_result_path=None,
                         show_plot=False):

        """考虑资金情况下的度量，进行与benchmark的收益度量对比，收益趋势，资金变动可视化，以及其它度量信息，不涉及benchmark"""
        result_path = os.path.join(save_result_path, 'result.txt') if save_result_path else save_result_path
        f = open(result_path, "w") if save_result_path else save_result_path

        self.log_func('买入后卖出的交易数量:{}'.format(self.order_has_ret.shape[0]), file=f)
        self.log_func('胜率:{:.4f}%'.format(self.win_rate * 100), file=f)

        self.log_func('平均获利期望:{:.4f}%'.format(self.gains_mean * 100), file=f)
        self.log_func('平均亏损期望:{:.4f}%'.format(self.losses_mean * 100), file=f)

        self.log_func('盈亏比:{:.4f}'.format(self.win_loss_profit_rate), file=f)

        self.log_func('策略收益: {:.4f}%'.format(self.algorithm_period_returns * 100), file=f)
        self.log_func('策略年化收益: {:.4f}%'.format(self.algorithm_annualized_returns * 100), file=f)

        self.log_func('策略夏普比率: {:.4f}'.format(self.algorithm_sharpe), file=f)
        self.log_func('策略最大回撤: {:.4f}%'.format(self.max_drawdown * 100), file=f)

        self.log_func('策略手续费: {:.4f}%'.format(self.capital.sum_commission / self.capital.read_cash * 100), file=f)
        self.log_func('策略滑点成本: {:.4f}%'.format(self._metrics_slippage_stats() / self.capital.read_cash * 100),
                      file=f)

        self.log_func('策略买入成交比例:{:.4f}%'.format(self.buy_deal_rate * 100), file=f)
        self.log_func('策略资金平均利用率比例:{:.4f}%'.format(self.cash_utilization * 100), file=f)
        self.log_func('策略资金最大利用率比例:{:.4f}%'.format(self.cash_max_utilization * 100), file=f)
        self.log_func('策略回测起始时间:{}, 结束时间:{}'.format(self.start_date, self.end_date), file=f)
        self.log_func('策略共执行{}个交易日'.format(self.num_trading_days), file=f)
        self.log_func(' ', file=f)
        if save_result_path:
            f.close()

        if only_info:
            return

        self.algorithm_cum_returns.plot()
        plt.legend(['algorithm returns'], loc='best')
        if save_plot_path:
            path = os.path.join(save_plot_path, 'return.png')
            plt.savefig(path)

        if show_plot:
            plt.show()

        plt.close()

        self.cash_utilization_series.plot()
        plt.legend(['cash utilization ratio'], loc='best')
        if save_plot_path:
            path = os.path.join(save_plot_path, 'cash_utilization_ratio.png')
            plt.savefig(path)

        if show_plot:
            plt.show()
        plt.close()

        if only_show_returns:
            return
        sns.regplot(x=np.arange(0, len(self.algorithm_cum_returns)), y=self.algorithm_cum_returns.values)
        plt.show()

        sns.distplot(self.capital.capital_pd['capital_blance'], kde_kws={"lw": 3, "label": "capital blance kde"})
        plt.show()

    @valid_check
    def plot_sharp_volatility_cmp(self, only_info=False):
        """sharp，volatility信息输出"""

        self.log_func('策略Sharpe夏普比率: {:.4f}'.format(self.algorithm_sharpe))
        self.log_func('策略波动率Volatility: {:.4f}'.format(self.algorithm_volatility))

    def _metrics_slippage_stats(self):
        """计算滑点产生的成本"""

        done_action_pd = self.action_pd[self.action_pd['deal']]

        def _cal_slippage(action):
            tick = AbuFuturesCn().query_contract_tick(action['symbol'])

            return tick * action['Cnt']

        sum_slippage = float(done_action_pd.apply(_cal_slippage, axis=1).sum())

        return sum_slippage

    def plot_option_analysis(self, save_plot_path=None, show_plot=False):
        """针对整个运行期间成交的期权进行统计分析"""

        for main_symbol in self.main_symbol_list:

            # print('main symbol: ', main_symbol)
            symbol_list = [key for key in self.mid_var_dict if key.startswith(main_symbol)]

            main_call_list = list()     # 品种看涨期权列表，例如‘TA‘
            main_put_list = list()      # 品种看跌期权列表，例如‘TA‘
            for symbol in symbol_list:
                call_list = self.mid_var_dict[symbol]['sell_factor_call']   # 特定品种合约看涨期权列表，例如‘TA1901’
                put_list = self.mid_var_dict[symbol]['sell_factor_put']     # 特定品种合约看跌期权列表，例如‘TA1901’

                main_call_list += call_list
                main_put_list += put_list

            call_index_list = list()
            call_maturity_list = list()
            call_profit_list = list()
            # print('call')
            for option in main_call_list:
                # if isinstance(option, list):
                #     for op in option:
                #         call_index_list.append(op.num_in_list)
                #         call_maturity_list.append(op.is_matured)
                #         call_profit_list.append(op.win)
                #
                #         # print(op)
                #         # print()
                # else:
                call_index_list.append(option.num_in_list)
                call_maturity_list.append(option.is_matured)
                call_profit_list.append(option.win)
                    # print(option)
                    # print()

            put_index_list = list()
            put_maturity_list = list()
            put_profit_list = list()
            # print('put')
            for option in main_put_list:

                # if isinstance(option, list):
                #     for op in option:
                #         put_index_list.append(op.num_in_list)
                #         put_maturity_list.append(op.is_matured)
                #         put_profit_list.append(op.win)
                #
                #         # print(op)
                #         # print()
                #
                # else:
                put_index_list.append(option.num_in_list)
                put_maturity_list.append(option.is_matured)
                put_profit_list.append(option.win)

                    # print(option)
                    # print()

            call_option_df = pd.DataFrame({main_symbol + '_call_idx': call_index_list, 'matured': call_maturity_list,
                                           'win': call_profit_list})

            put_option_df = pd.DataFrame({main_symbol + '_put_idx': put_index_list, 'matured': put_maturity_list,
                                          'win': put_profit_list})

            plt.figure()
            sns.catplot(x=main_symbol + '_call_idx', hue="win", col="matured", data=call_option_df, kind="count")
            if save_plot_path:
                path = os.path.join(save_plot_path, '{:s}_call_idx.png'.format(main_symbol))
                plt.savefig(path)

            if show_plot:
                plt.show()
            plt.close()

            plt.figure()
            sns.catplot(x=main_symbol + '_put_idx', hue="win", col="matured", data=put_option_df, kind="count")
            if save_plot_path:
                path = os.path.join(save_plot_path, '{:s}_put_idx.png'.format(main_symbol))
                plt.savefig(path)

            if show_plot:
                plt.show()
            plt.close()

    def make_options_pd(self):

        options_pd = pd.DataFrame(columns=['initial_datetime', 'symbol', 'strike_price', 'maturity_days',
                                           'initial_vol', 'option_type', 'direction',
                                           'num_in_list', 'nominal_numbers', 'initial_value',
                                           'matured_price', 'clear_price', 'clear_datetime',
                                           'maturity_date', 'outstanding_days', 'is_matured',
                                           'win_or_loss', 'profit'
                                           ])

        for symbol in self.mid_var_dict:
            call_option_list = self.mid_var_dict[symbol]['sell_factor_call']
            put_option_list = self.mid_var_dict[symbol]['sell_factor_put']

            ret_call_options_pd = pd.DataFrame(columns=['initial_datetime', 'symbol', 'strike_price', 'maturity_days',
                                                        'initial_vol', 'option_type', 'direction',
                                                        'num_in_list', 'nominal_numbers', 'initial_value',
                                                        'matured_price', 'clear_price', 'clear_datetime',
                                                        'maturity_date', 'outstanding_days', 'is_matured',
                                                        'win_or_loss', 'profit'
                                                        ])

            ret_put_options_pd = pd.DataFrame(columns=['initial_datetime', 'symbol', 'strike_price', 'maturity_days',
                                                       'initial_vol', 'option_type', 'direction',
                                                       'num_in_list', 'nominal_numbers', 'initial_value',
                                                       'matured_price', 'clear_price', 'clear_datetime',
                                                       'maturity_date', 'outstanding_days', 'is_matured',
                                                       'win_or_loss', 'profit'
                                                       ])

            for index, option in enumerate(call_option_list):
                # 迭代call_option，将每一个AbuOption对象转换为一个pd.DataFrame对象

                call_option_pd = pd.DataFrame(np.array([option.initial_datetime, option.symbol, option.k,
                                                        option.maturity_days, option.vol, option.cp,
                                                        option.direction, option.num_in_list, option.num,
                                                        option.initial_value, option.matured_price, option.clear_price,
                                                        option.clear_datetime, option.maturity_date, option.last_days,
                                                        option.is_matured, option.win, option.profit]).reshape(1, -1),
                                              index=[index],
                                              columns=['initial_datetime', 'symbol', 'strike_price', 'maturity_days',
                                                       'initial_vol', 'option_type', 'direction',
                                                       'num_in_list', 'nominal_numbers', 'initial_value',
                                                       'matured_price', 'clear_price', 'clear_datetime',
                                                       'maturity_date', 'outstanding_days', 'is_matured',
                                                       'win_or_loss', 'profit'
                                                       ])

                ret_call_options_pd = ret_call_options_pd.append(call_option_pd, ignore_index=True)

            for index, option in enumerate(put_option_list):
                # 迭代put_option，将每一个AbuOption对象转换为一个pd.DataFrame对象
                put_option_pd = pd.DataFrame(np.array([option.initial_datetime, option.symbol, option.k,
                                                       option.maturity_days, option.vol, option.cp,
                                                       option.direction, option.num_in_list, option.num,
                                                       option.initial_value, option.matured_price, option.clear_price,
                                                       option.clear_datetime, option.maturity_date, option.last_days,
                                                       option.is_matured, option.win, option.profit]).reshape(1, -1),
                                             index=[index],
                                             columns=['initial_datetime', 'symbol', 'strike_price', 'maturity_days',
                                                      'initial_vol', 'option_type', 'direction',
                                                      'num_in_list', 'nominal_numbers', 'initial_value',
                                                      'matured_price', 'clear_price', 'clear_datetime',
                                                      'maturity_date', 'outstanding_days', 'is_matured',
                                                      'win_or_loss', 'profit'
                                                      ])

                ret_put_options_pd = ret_put_options_pd.append(put_option_pd, ignore_index=True)

            ret_options_pd = pd.concat([ret_call_options_pd, ret_put_options_pd], ignore_index=True)
            options_pd = options_pd.append(ret_options_pd, ignore_index=True)

        options_pd['option_type'] = options_pd['option_type'].astype(int)
        options_pd['direction'] = options_pd['direction'].astype(int)

        options_pd['option_type'] = np.where(options_pd['option_type'] == 1, 'CALL', 'PUT')
        options_pd['direction'] = np.where(options_pd['direction'] == 1, 'BUY', 'SELL')

        options_pd = options_pd.sort_values(['initial_datetime'])
        options_pd.reset_index(drop=True, inplace=True)

        return options_pd
