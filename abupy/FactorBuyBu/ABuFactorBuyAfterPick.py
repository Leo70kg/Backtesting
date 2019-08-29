# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuFactorBuyBase import AbuFactorBuyBase, BuyCallMixin, BuyPutMixin


# noinspection PyAttributeOutsideInit
class AbuFactorBuyAfterPick(AbuFactorBuyBase, BuyCallMixin):
    """示例正向突破买入择时类，混入BuyCallMixin，即向上突破触发买入event"""

    def _init_self(self, **kwargs):

        self.pick_period = kwargs['pick_period']
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}'.format(self.__class__.__name__)

    def fit_day(self, today):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :return:
        """
        if self.pick_period == 'month':
            if today.month_task == 1:
                return self.buy_tomorrow()

        elif self.pick_period == 'week':
            if today.week_task == 1:
                return self.buy_tomorrow()

        else:
            return self.buy_tomorrow()


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutAfterPick(AbuFactorBuyBase, BuyPutMixin):
    """示例反向突破买入择时类，BuyPutMixin，即向下突破触发买入event"""

    def _init_self(self, **kwargs):

        self.pick_period = kwargs['pick_period']
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}'.format(self.__class__.__name__)

    def fit_day(self, today):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :return:
        """
        if self.pick_period == 'month':
            if today.month_task == 1:
                return self.buy_tomorrow()

        elif self.pick_period == 'week':
            if today.week_task == 1:
                return self.buy_tomorrow()

        else:
            return self.buy_tomorrow()
