# -*- encoding:utf-8 -*-
"""
    卖出择时示例因子：突破卖出择时因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from .ABuFactorSellBase import AbuFactorSellBase, AbuFactorSellXD, ESupportDirection
from ..UtilBu.ABuKlineUtil import min_kline
from ..UtilBu.ABuStrUtil import get_num_from_str

__author__ = '阿布'
__weixin__ = 'abu_quant'


class AbuFactorSellBreak(AbuFactorSellBase):
    """示例向下突破卖出择时因子"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""

        # 向下突破参数 xd， 比如20，30，40天...突破
        self.xd = kwargs['xd']
        # 在输出生成的orders_pd中显示的名字
        self.sell_type_extra = '{}:{}'.format(self.__class__.__name__, self.xd)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = get_num_from_str(kwargs['freq'])
        # 输出根据特定频率下合成的行情数据
        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def fit_day(self, today, holding_cnt, orders):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        """
        _check_freq = self.check_freq_today(today, self.freq)

        if not _check_freq:
            return orders, 0

        else:
            today_ind = int(self.freq_kl_pd[self.freq_kl_pd.datetime == today.datetime].key.values[0])
            # condition = today.close == self.kl_pd.close[self.today_ind - self.xd + 1:self.today_ind + 1].min()
            condition = today.close == self.freq_kl_pd.close[today_ind - self.xd + 1:today_ind + 1].min()

            return self.sell_tomorrow_orders(condition, orders, holding_cnt)


class AbuFactorSellXDBK(AbuFactorSellXD):
    """示例继承AbuFactorBuyXD, 向下突破卖出择时因子"""

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def fit_day(self, today, orders):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param orders: 买入择时策略中生成的订单序列
        """
        # 今天的收盘价格达到xd天内最低价格则符合条件
        if today.close == self.xd_kl.close.min():
            for order in orders:
                self.sell_tomorrow(order)
