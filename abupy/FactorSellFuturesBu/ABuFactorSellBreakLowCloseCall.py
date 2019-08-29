# -*- encoding:utf-8 -*-
"""
    突破均线后平仓因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import numpy as np

from .ABuFactorSellFuturesBase import AbuFactorSellFuturesBase, ESupportDirection


class AbuFactorSellBreakLowCloseCall(AbuFactorSellFuturesBase):
    """到期平仓卖出因子"""

    def _init_self(self, **kwargs):

        self.xd = kwargs['xd']
        # 卖出仓位的百分比
        self.sell_pct = kwargs['sell_pct']
        # 在输出生成的orders_pd中显示的名字
        self.sell_type_extra = '{}:{}'.format(self.__class__.__name__, self.xd)

        self.freq = kwargs['freq'].upper()
        self.freq_kl_pd, self.kline_num = self.get_freq_kl_pd(self.kl_pd, self.freq, self.kl_pd_dict)

        self.low_ndarray = self.freq_kl_pd.low.values
        self.high_ndarray = self.freq_kl_pd.high.values

        self.today_time_str = self.get_today_time_str(self.freq)

        self.freq_kl_pd_time_str = self.get_freq_kl_pd_time_str(self.freq)
        self.time_ndarray = self.freq_kl_pd[self.freq_kl_pd_time_str].values

    def read_fit_day(self, today, undone_orders, holding_object, buy_factor):

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.key)
        done_orders = list()

        if buy_factor.holding_cnt == 0:
            return done_orders, undone_orders, None

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        # orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, undone_orders, holding_object, buy_factor)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def fit_day(self, today, orders, holding_object, buy_factor):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_object: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :param buy_factor: 实例化的买入因子
        """

        today_ind = np.where(self.time_ndarray == today[self.today_time_str])[0][0]

        if today_ind < self.xd:
            return [], orders, None

        low = self.low_ndarray[today_ind - self.xd: today_ind].min()
        high = self.high_ndarray[today_ind - self.xd: today_ind].max()

        condition = today.close < (high + low) / 2

        if condition:
            for option in buy_factor.option_list:
                option.profit = (np.maximum((today.close - option.k) * option.cp, 0) - option.initial_value) * \
                                option.num
                option.win = True if option.profit > 0 else False

            option_cleared_list = buy_factor.option_list

            buy_factor.option_list = list()

            self.sell_cnt = buy_factor.holding_cnt * self.sell_pct

            done_orders, undone_orders = self.sell_tomorrow(orders, holding_object, buy_factor)

            return done_orders, undone_orders, option_cleared_list

        else:
            return [], orders, None
