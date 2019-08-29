# -*- coding: utf-8 -*-
# Leo70kg
"""
欧式期权对冲买入因子
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from .ABuFactorSellFuturesBase import AbuFactorSellFuturesBase, ESupportDirection


# noinspection PyAttributeOutsideInit
class AbuFactorSellOptionHedge(AbuFactorSellFuturesBase):
    """示例向下突破卖出择时因子"""

    def _init_self(self, **kwargs):
        """
        :param buy_factor:实例化买入因子，适用于买入因子的专属卖出因子
        :param kwargs:
        :return:
        """
        self.hedge_threshold = kwargs['threshold']
        # self.option_list_name = kwargs['option_info_list']

        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}'.format(self.__class__.__name__)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        # self.freq = kwargs['freq'].upper()
        # 输出根据特定频率下合成的行情数据
        # self.freq_kl_pd, self.kline_num = self.get_freq_kl_pd(self.kl_pd, self.freq, self.kl_pd_dict)

        # 载入特定合约的波动率表
        # self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.kl_pd.name))

    def read_fit_day(self, today, undone_orders, holding_object, buy_factor):

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.values[14])
        # 回测中默认忽略最后一个交易日
        # if self.today_ind >= self.kl_pd.shape[0] - 1:
        #     done_orders = list()
        #
        #     return done_orders, undone_orders, None

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        # orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, undone_orders, holding_object, buy_factor)

    def support_direction(self):
        """支持的方向，支持正向和反向"""
        return [ESupportDirection.DIRECTION_CAll.value, ESupportDirection.DIRECTION_PUT.value]

    def fit_day(self, today, orders, holding_object, buy_factor):

        matured_option = None

        if buy_factor.option_list:
            cnt = 0

            is_maturity = False
            for i in range(len(buy_factor.option_list)):
                option = buy_factor.option_list[i]
                # print(today.datetime, i, option.t, option.maturity_date)

                delta = option.delta

                if option.last_days == 0:
                    option.profit = (np.maximum((today.close - option.k) * option.cp, 0) - option.initial_value) * \
                                    option.num * option.direction

                    option.win = 1 if option.profit > 0 else 0
                    option.is_matured = 1
                    option.matured_price = today.close
                    option.maturity_date = today.date
                    option.clear_datetime = today.datetime

                    is_maturity = True
                    matured_option = option
                    # buy_factor.matured_option_list.append(option)
                    maturity_id = i
                    continue

                cnt += abs(delta)

            if is_maturity:
                del buy_factor.option_list[maturity_id]

            threshold_cnt = self.hedge_threshold * cnt

            condition = buy_factor.holding_cnt - cnt > threshold_cnt
            self.sell_cnt = buy_factor.holding_cnt - cnt if condition else 0

            # if self.kl_pd.name == 'C1801' and today.date>20180103:
            #     print(today.date, today.datetime, 'holding_cnt: ', buy_factor.holding_cnt, 'cnt: ', cnt,
            #     'threshold_cnt: ', threshold_cnt, 'sell_cnt: ', self.sell_cnt)

            if condition:

                done_orders, undone_orders = self.sell_tomorrow(orders, holding_object, buy_factor)

                return done_orders, undone_orders, matured_option

        return [], orders, matured_option
