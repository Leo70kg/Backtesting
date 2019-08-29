# -*- encoding:utf-8 -*-
"""
    突破均线后平仓因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from .ABuFactorSellBase import AbuFactorSellBase, ESupportDirection
from ..UtilBu.ABuKlineUtil import min_kline
from ..UtilBu.ABuStrUtil import get_num_from_str, get_letters
from ..CoreBu.ABuEnv import g_futures_kline_num_dict
from ..IndicatorBu.ABuNDMa import calc_ma_from_prices


class AbuFactorSellBreakMACloseCallPosition(AbuFactorSellBase):
    """到期平仓卖出因子"""

    def _init_self(self, **kwargs):

        self.xd = kwargs['xd']
        # 卖出仓位的百分比
        self.sell_pct = kwargs['sell_pct']
        # 在输出生成的orders_pd中显示的名字
        self.sell_type_extra = '{}:{}'.format(self.__class__.__name__, self.xd)

        self.freq = get_num_from_str(kwargs['freq'])
        self.kline_num = g_futures_kline_num_dict[kwargs['freq']][get_letters(self.kl_pd.name)]

        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

        self.ma_line = calc_ma_from_prices(self.freq_kl_pd.close, int(self.xd * self.kline_num), min_periods=1)

    def read_fit_day(self, today, holding_cnt, orders, buy_factor):

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.key)
        # 回测中默认忽略最后一个交易日
        if self.today_ind >= self.kl_pd.shape[0] - 1:
            return orders, 0

        if holding_cnt == 0:
            return orders, 0

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, holding_cnt, orders, buy_factor)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def fit_day(self, today, holding_cnt, orders, buy_factor):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :param buy_factor: 实例化的买入因子
        """

        if self.today_ind < self.xd * self.kline_num - 1:
            return orders, 0

        # condition = today.close < self.ma_line[today_ind - self.xd + 1:today_ind + 1].max()
        condition = today.close < self.ma_line[self.today_ind]
        if condition:
            buy_factor.signal_list = list()
            print()
            print(today.date)
            print('sell all call!!!!!!!!!!!!!')

            self.sell_cnt = holding_cnt * self.sell_pct if condition else 0
            print('sell_cnt: ', self.sell_cnt)
            print()

            return self.sell_tomorrow_orders(condition, orders, holding_cnt)

        else:
            return orders, 0