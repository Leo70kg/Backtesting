# -*- encoding:utf-8 -*-
"""
    买入择时示例因子：突破买入择时因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from .ABuFactorBuyBase import AbuFactorBuyBase, AbuFactorBuyXD, BuyCallMixin, BuyPutMixin
from ..UtilBu.ABuKlineUtil import min_kline
from ..UtilBu.ABuStrUtil import get_num_from_str

__author__ = '阿布'
__weixin__ = 'abu_quant'


# noinspection PyAttributeOutsideInit
class AbuFactorBuyBreak(AbuFactorBuyBase, BuyCallMixin):
    """示例正向突破买入择时类，混入BuyCallMixin，即向上突破触发买入event"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:{}'.format(self.__class__.__name__, self.xd)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = get_num_from_str(kwargs['freq'])
        # 输出根据特定频率下合成的行情数据
        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

    def fit_day(self, today, holding_cnt):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 交易发生之前的持仓量
        :return:
        """
        _check_if = self.check_dominant_today(today)
        _check_freq = self.check_freq_today(today, self.freq)

        if not _check_if:
            return None

        if not _check_freq:
            return None

        today_ind = int(self.freq_kl_pd[self.freq_kl_pd.datetime == today.datetime].key.values[0])
        # print(self.kl_pd.name)
        # print(today_ind)
        # 忽略不符合买入的天（统计周期内前xd天）
        if today_ind < self.xd - 1:

            return None
        # 今天的收盘价格达到xd天内最高价格则符合买入条件

        if today.close == self.freq_kl_pd.close[today_ind - self.xd + 1:today_ind + 1].max():
            # 把突破新高参数赋值skip_days，这里也可以考虑make_buy_order确定是否买单成立，但是如果停盘太长时间等也不好
            self.skip_days = self.xd * self.freq
            # 生成买入订单, 由于使用了今天的收盘价格做为策略信号判断，所以信号发出后，只能明天买
            return self.buy_tomorrow(holding_cnt)

        return None

        # 忽略不符合买入的天（统计周期内前xd天）
        # if self.today_ind < self.xd - 1:
        #     return None
        #
        # # 今天的收盘价格达到xd天内最高价格则符合买入条件
        # if today.close == self.kl_pd.close[self.today_ind - self.xd + 1:self.today_ind + 1].max():
        #     # 把突破新高参数赋值skip_days，这里也可以考虑make_buy_order确定是否买单成立，但是如果停盘太长时间等也不好
        #     self.skip_days = self.xd
        #     # 生成买入订单, 由于使用了今天的收盘价格做为策略信号判断，所以信号发出后，只能明天买
        #     return self.buy_tomorrow(holding_cnt)
        # return None


# noinspection PyAttributeOutsideInit
class AbuFactorBuyXDBK(AbuFactorBuyXD, BuyCallMixin):
    """示例继承AbuFactorBuyXD完成正向突破买入择时类"""
    def fit_day(self, today):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :return:
        """
        # 今天的收盘价格达到xd天内最高价格则符合买入条件
        if today.close == self.xd_kl.close.max():
            return self.buy_tomorrow()
        return None


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutBreak(AbuFactorBuyBase, BuyPutMixin):
    """示例反向突破买入择时类，混入BuyPutMixin，即向下突破触发买入event，详情请查阅期货回测示例demo"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""

        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        self.factor_name = '{}:{}'.format(self.__class__.__name__, self.xd)

    def fit_day(self, today, holding_cnt):
        """
        针对每一个交易日拟合买入交易策略，寻找向下突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 交易发生之前的持仓量
        :return:
        """
        # 忽略不符合买入的天（统计周期内前xd天）
        if self.today_ind < self.xd - 1:
            return None
        """
            与AbuFactorBuyBreak区别就是买向下突破的，即min()
        """
        if today.close == self.kl_pd.close[self.today_ind - self.xd + 1:self.today_ind + 1].min():
            self.skip_days = self.xd
            return self.buy_tomorrow(holding_cnt)
        return None


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutXDBK(AbuFactorBuyXD, BuyPutMixin):
    """示例继承AbuFactorBuyXD完成反向突破买入择时类"""
    def fit_day(self, today):
        """
        针对每一个交易日拟合买入交易策略，寻找向上突破买入机会
        :param today: 当前驱动的交易日金融时间序列数据
        :return:
        """
        # 与AbuFactorBuyBreak区别就是买向下突破的，即min()
        if today.close == self.xd_kl.close.min():
            return self.buy_tomorrow()
        return None
