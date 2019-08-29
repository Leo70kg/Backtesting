# -*- coding: utf-8 -*-
# Leo70kg
"""
    示例仓位管理：欧式期权对冲仓位管理模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuPositionBase import AbuPositionBase


class AbuEuroOptionHedgeSellPosition(AbuPositionBase):
    """欧式期权对冲仓位管理类"""

    def fit_position(self, factor_object):
        """
        fit_position计算的结果是买入多少个单位（股，手，顿，合约）
        计算：（常数价格 ／ 买入价格）＊ 当天交易日atr21
        :param factor_object: ABuFactorBuyBases实例对象
        :return: 买入多少个单位（股，手，顿，合约）
        """

        return factor_object.sell_cnt

    def _init_self(self, **kwargs):
        """不断更新持仓设置"""

