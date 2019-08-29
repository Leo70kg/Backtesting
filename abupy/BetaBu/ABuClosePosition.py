# -*- coding: utf-8 -*-
# Leo70kg
"""
    固定仓位管理：特定数量仓位管理模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuPositionBase import AbuPositionBase


class AbuClosePosition(AbuPositionBase):

    def fit_position(self, factor_object):
        """
        fit_position计算的结果是买入多少个单位（股，手，顿，合约）
        计算：（常数价格 ／ 买入价格）＊ 当天交易日atr21
        :param factor_object: ABuFactorBuyBases实例对象
        :return: 买入多少个单位（股，手，顿，合约）
        """
        return self.holding_cnt

    def _init_self(self):
        pass
