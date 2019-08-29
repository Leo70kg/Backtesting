# -*- coding: utf-8 -*-
# Leo70kg
"""
欧式期权对冲买入因子，分为买入看涨期权和买入看跌期权
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuFactorBuyBase import AbuFactorBuyBase, BuyCallMixin, BuyPutMixin
from ..UtilBu import ABuEuroOptionUtil


s_threshold = 0.05


# noinspection PyAttributeOutsideInit
class AbuFactorBuyEuroOptionHedge(AbuFactorBuyBase, BuyCallMixin):
    """示例正向对冲买入择时类，混入BuyCallMixin，即向上突破触发买入event, 适用于看涨期权"""

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

    def fit_day(self, today, holding_cnt):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 交易发生之前的持仓量
        :return:
        """

        # TODO 波动率根据当天日期从表中获取

        _check_if = self.check_dominant_today(today)

        if not _check_if:
            return None

        # 当delta值超过一定的阈值就触发买入
        s = today.close
        delta = ABuEuroOptionUtil.bs_delta(s, self.strike, self.rate, self.dividend, self.maturity, self.volatility,
                                           self.cp, self.date_type)

        cnt = self.nominal_num * delta
        hc = self.expect_direction * holding_cnt

        if cnt - hc > s_threshold * cnt:
            return self.buy_tomorrow(holding_cnt)
        return None


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutEuroOptionHedge(AbuFactorBuyBase, BuyPutMixin):
    """示例反向对冲买入择时类，混入BuyPutMixin，即向下突破触发买入event, 适用于看跌期权"""

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
        self.factor_name = '{}:{}'.format(self.__class__.__name__, self.xd)

    def fit_day(self, today, holding_cnt):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 交易发生之前的持仓量
        :return:
        """
        _check_if = self.check_dominant_today(today)

        if not _check_if:
            return None

        # 忽略不符合买入的天（统计周期内前xd天）
        if self.today_ind < self.xd - 1:
            return None

        # 当delta值超过一定的阈值就触发买入
        s = today.close
        delta = ABuEuroOptionUtil.bs_delta(s, self.strike, self.rate, self.dividend, self.maturity, self.volatility,
                                           self.cp, self.date_type)

        cnt = self.nominal_num * delta
        hc = self.expect_direction * holding_cnt

        if cnt - hc < s_threshold * cnt:
            return self.buy_tomorrow(holding_cnt)
        return None
