# -*- coding: utf-8 -*-
# Leo70kg
"""
    仓位管理：根据标的资产波动率进行仓位管理模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math

from ..MarketBu.ABuSymbolFutures import AbuFuturesCn
from .ABuPositionBase import AbuPositionBase


class AbuVolatilityPosition(AbuPositionBase):
    """波动率仓位管理类"""

    s_init_money = 300000

    def fit_position(self, factor_object):
        """
        fit_position计算的结果是买入多少个单位（股，手，顿，合约）
        计算：（固定金额 ／ 买入价格 ／ 波动率）
        :param factor_object: ABuFactorBuyBases实例对象
        :return: 买入多少个单位（股，手，顿，合约）
        """
        return math.floor(self.init_money / self.vol / self.bp / self.min_unit) * self.min_unit

    def _init_self(self, **kwargs):
        """volatility仓位控制管理类初始化设置"""
        q_df = AbuFuturesCn().query_symbol(self.symbol_name)
        if q_df is not None:
            # 每手单位数量
            s_min_unit = q_df.min_unit.values[0]

        # self.n_assets = kwargs.pop('n_assets', AbuVolatilityPosition.n_assets)
        self.vol = kwargs.pop('volatility', self.kl_pd_buy.vol)
        self.init_money = kwargs.pop('init_money', AbuVolatilityPosition.s_init_money)
        self.min_unit = kwargs.pop('min_unit', s_min_unit)
