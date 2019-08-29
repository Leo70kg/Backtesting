# -*- coding: utf-8 -*-
# Leo70kg
"""
欧式期权对冲买入因子
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuFactorSellBase import AbuFactorSellBase, ESupportDirection
from ..UtilBu.ABuKlineUtil import min_kline
from ..UtilBu import ABuEuroOptionUtil
from ..UtilBu.ABuStrUtil import get_letters, get_num_from_str
from ..CoreBu.ABuEnv import g_trade_date_list, g_futures_kline_num_dict

s_threshold = 0.05


# noinspection PyAttributeOutsideInit
class AbuFactorSellOptionHedgeMin(AbuFactorSellBase):
    """示例向下突破卖出择时因子"""

    def _init_self(self, **kwargs):
        """
        :param buy_factor:实例化买入因子，适用于买入因子的专属卖出因子
        :param kwargs:
        :return:
        """
        self.signal_list = kwargs['option_info_list']

        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}'.format(self.__class__.__name__)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = get_num_from_str(kwargs['freq'])
        self.kline_num = g_futures_kline_num_dict[kwargs['freq']][get_letters(self.kl_pd.name)]
        # 输出根据特定频率下合成的行情数据
        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

        # 载入特定合约的波动率表
        self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.kl_pd.name))

    def read_fit_day(self, today, holding_cnt, orders, buy_factor):

        self.option_info_list = getattr(buy_factor, self.signal_list)

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.key)
        # 回测中默认忽略最后一个交易日
        if self.today_ind >= self.kl_pd.shape[0] - 1:
            return orders, 0

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, holding_cnt, orders)

    def support_direction(self):
        """支持的方向，支持正向和反向"""
        return [ESupportDirection.DIRECTION_CAll.value, ESupportDirection.DIRECTION_PUT.value]

    def fit_day(self, today, holding_cnt, orders):

        if self.option_info_list:

            yesterday_date = g_trade_date_list[g_trade_date_list.index(today.date) - 1]

            s = today.close
            print('sell_strategy')
            print(today.date)
            print(today.datetime)
            print(self.option_info_list)
            cnt = 0
            for option_info_dict in self.option_info_list:

                k = option_info_dict['strike']
                r = option_info_dict['rate']
                q = option_info_dict['dividend']
                t = g_trade_date_list.index(option_info_dict['maturity_date']) - g_trade_date_list.index(today.date)
                cp = option_info_dict['cp']
                date_type = option_info_dict['date_type']
                direction = option_info_dict['direction']
                num = option_info_dict['nominal_num']
                vol = self.vol_df.loc[yesterday_date, 'Close_to_Close_Vol']

                self.delta = 0 if t < 1 else ABuEuroOptionUtil.bs_delta(s, k, r, q, t, vol, cp, date_type) * direction

                # print('delta')
                # print(delta)

                cnt += abs(num * self.delta)

            print('cnt: ', cnt)
            print('********')
            print()

            hc = holding_cnt

            condition = hc - cnt > s_threshold * cnt
            self.sell_cnt = hc - cnt if condition else 0

            return self.sell_tomorrow_orders(condition, orders, holding_cnt)

        return orders, 0
