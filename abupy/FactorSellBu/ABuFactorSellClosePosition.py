# -*- encoding:utf-8 -*-
"""
    期货合约到期平仓因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from .ABuFactorSellBase import AbuFactorSellBase, ESupportDirection
from ..CoreBu.ABuEnv import g_futures_cn_date_dict


class AbuFactorSellClosePosition(AbuFactorSellBase):
    """到期平仓卖出因子"""

    def _init_self(self, **kwargs):
        # 在输出生成的orders_pd中显示的名字
        self.sell_type_extra = '{}'.format(self.__class__.__name__)

        # # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        # self.freq = get_num_from_str(kwargs['freq'])
        # # 输出根据特定频率下合成的行情数据
        # self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

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
        symbol = self.kl_pd.name

        end_date = g_futures_cn_date_dict[symbol][1]

        condition = today.date > end_date
        return self.sell_tomorrow_orders(condition, orders, holding_cnt)
