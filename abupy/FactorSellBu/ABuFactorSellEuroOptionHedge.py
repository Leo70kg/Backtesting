# -*- coding: utf-8 -*-
# Leo70kg
"""
欧式期权对冲买入因子
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuFactorSellBase import AbuFactorSellBase, ESupportDirection
from ..UtilBu import ABuEuroOptionUtil

s_threshold = 0.05


# noinspection PyAttributeOutsideInit
class AbuFactorSellEuroOptionHedge(AbuFactorSellBase):
    """示例向下突破卖出择时因子"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 期权各参数"""

        self.strike = kwargs['strike']
        self.rate = kwargs['rate']
        self.dividend = kwargs['dividend']
        self.maturity = kwargs['maturity']
        self.volatility = kwargs['volatility']
        self.cp = kwargs['cp']
        self.date_type = kwargs['date_type']
        self.nominal_num = kwargs['nominal_num']

        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:strike_{}'.format(self.__class__.__name__, self.strike)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value, ESupportDirection.DIRECTION_PUT.value]

    def fit_day(self, today, holding_cnt, orders):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 交易发生之前的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :return:
        """
        revised_order_list = []
        sell_cnt_list = []

        # 当delta值超过一定的阈值就触发买入
        s = today.close
        self.delta = ABuEuroOptionUtil.bs_delta(s, self.strike, self.rate, self.dividend, self.maturity,
                                                self.volatility, self.cp, self.date_type)
        print('********')
        print('sell')
        print(self.delta)
        cnt = self.nominal_num * self.delta
        hc = self.cp * holding_cnt
        thresh = self.cp * (hc - cnt)

        print(thresh)
        print(s_threshold * cnt)
        print('********')
        condition = thresh > s_threshold * cnt

        return self.sell_tomorrow_orders(condition, orders, holding_cnt)
