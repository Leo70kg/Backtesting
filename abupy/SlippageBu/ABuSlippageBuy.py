# -*- coding: utf-8 -*-
# Leo70kg
"""
    日内滑点买入示例实现：以第二天开盘价向上设置n个滑点为实际成交价格
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from .ABuSlippageBuyBase import AbuSlippageBuyBase, slippage_limit_up


class AbuSlippageBuyMean(AbuSlippageBuyBase):
    """示例日内滑点均价买入类"""

    @slippage_limit_up
    def fit_price(self, n=2):
        """
        取一分钟交易数据的最高最低均价并加上n个tick做为决策价格
        :return: 最终决策的当前交易买入价格
        """

        # 买入价格为当天均价，即最高，最低的平均，也可使用高开低收平均等方式计算
        self.buy_price = np.mean([self.kl_pd_buy['high'], self.kl_pd_buy['low']]) + n * self.kl_pd_buy.name
        # 返回最终的决策价格
        return self.buy_price