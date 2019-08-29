# -*- encoding:utf-8 -*-
"""
    日内滑点卖出空头示例实现：以n个滑点成交
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ..MarketBu.ABuSymbolFutures import AbuFuturesCn
from .ABuSlippageSellBase import AbuSlippageSellBase, slippage_limit_down

"""默认一个滑点"""
g_tick_num = 1


class AbuSlippageSellPutTick(AbuSlippageSellBase):

    @slippage_limit_down
    def fit_price(self):
        """
        :return: 最终决策的当前交易卖出价格
        """
        tick_size = AbuFuturesCn().query_contract_tick(self.symbol)

        self.sell_price = self.kl_pd_sell['close'] + g_tick_num * tick_size
        # 返回最终的决策价格
        return self.sell_price
