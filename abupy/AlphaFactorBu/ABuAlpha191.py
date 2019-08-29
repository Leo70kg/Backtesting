# -*- encoding:utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division

import numpy as np
import pandas as pd
from ..UtilBu import ABuDataFrameUtil, ABuMySQLUtil


class AbuAlpha191(object):

    @classmethod
    def alpha001(cls, symbol, end_date=None):
        """end_date默认为None，即计算最近一天的因子值"""

        """获取对应标的的时间序列，形式为DataFrame"""
        _symbol = ABuMySQLUtil.WindMysqlApi(symbol)
        df = _symbol.kline(end=end_date)

        c1 = df.volume.apply(np.log).diff(1)
        c2 = (df.close - df.open) / df.open
        rank1 = c1.rank()
        rank2 = c2.rank()

        corr = pd.rolling_corr(rank1, rank2, 6)
        result = -corr.iloc[-1]

        return result

    @classmethod
    def alpha002(cls):

        c1 = (self.close - self.low) - (self.high - self.close)
        c2 = self.high - self.low
        c3 = c1 / c2

        result = -(c3.diff(1))

        return result

    def alpha003(self):

        pre_close = self.close.shift(1)
        c1 = np.minimum(self.low, pre_close)
        c2 = np.maximum(self.high, pre_close)

        c3 = ABuDataFrameUtil.if_else_func(self.close > pre_close, c1, c2)
        result = ABuDataFrameUtil.if_else_func(self.close == pre_close, 0, self.close - c3)

        return result

    def alpha004(self):

        c1 = self.close.rolling(8).sum() / 8
        c2 = self.close.rolling(2).sum() / 2
        c3 = self.close.rolling(8).std()
        c4 = self.volume / self.volume.rolling(20).mean()

        con1 = c4 >= 1
        c5 = ABuDataFrameUtil.if_else_func(con1, 1, -1)

        con2 = c2 < (c1 - c3)
        c6 = ABuDataFrameUtil.if_else_func(con2, 1, c5)

        con3 = (c1 + c3) < c2
        result = ABuDataFrameUtil.if_else_func(con3, -1, c6)

        return result

    def alpha005(self):

        c1 = ABuDataFrameUtil.rolling_rank(self.volume, 5)
        c2 = ABuDataFrameUtil.rolling_rank(self.high, 5)

        corr = pd.rolling_corr(c1, c2, 5)
        result = -(corr.rolling(3).max())

        return result

    def alpha006(self):

        c1 = self.open * 0.85 + self.high * 0.15
        c2 = c1.diff(4)

        c3 = np.sign(c2)
        return c3.rank()

    def alpha007(self):

        c1 = np.maximum(self.vwap - self.close, 3)
        c2 = np.minimum(self.vwap - self.close, 3)
        c3 = self.volume.diff(3)

        result = (c1.rank() + c2.rank()) * c3.rank()

        return result

    def alpha008(self):

        c1 = (self.high + self.low) / 2 * 0.2 + (self.vwap * 0.8)
        c2 = c1.diff(4) * -1

        result = c2.rank()

        return result

    def alpha009(self):

        c1 = (self.high.shift(1) + self.low.shift(1)) / 2
        c2 = (self.high + self.low) / 2
        c3 = (self.high - self.low) / self.volume

        return ABuDataFrameUtil.sma((c2 - c1) * c3, 7, 2)

    def alpha010(self):

        c1 = self.ret.rolling(20).std()

        c2 = (ABuDataFrameUtil.if_else_func(self.ret < 0, c1, self.close)) ** 2
        c3 = c2.rolling(5).max()

        c4 = c3.rank()

        return c4

    def alpha011(self):

        c1 = (self.close - self.low) - (self.high - self.close)
        c2 = c1 / (self.high - self.low) * self.volume
        c3 = c2.rolling(6).sum()

        return c3

    def alpha012(self):

        c1 = self.vwap.rolling(10).sum() / 10
        c2 = self.open - c1
        c3 = c2.rank()

        c4 = np.abs(self.close - self.vwap)
        c5 = -(c4.rank())

        result = c3 * c5

        return result

    def alpha013(self):

        c1 = self.high - self.low
        c2 = c1 ** 0.5 - self.vwap

        return c2

    def alpha014(self):

        return self.close - self.close.shift(5)

    def alpha015(self):

        result = self.open / self.close.shift(1) - 1

        return result

    def alpha016(self):

        c1 = self.volume.rank()
        c2 = self.vwap.rank()

        c3 = c1.rolling(5).corr(c2)
        c4 = c3.rank()
        c5 = -(c4.rolling(5).max())

        return c5

    def alpha017(self):

        c1 = np.maximum(self.vwap, 15)
        c2 = (self.vwap - c1).rank()
        c3 = self.close.diff(5)

        result = c2 ** c3

        return result

    def alpha018(self):

        result = self.close / self.close.shift(5)

        return result

    def alpha019(self):

        condition1 = (self.close == self.close.shift(5))
        c1 = (self.close - self.close.shift(5)) / self.close
        c2 = ABuDataFrameUtil.if_else_func(condition1, 0, c1)

        condition2 = (self.close < self.close.shift(5))
        c3 = (self.close - self.close.shift(5)) / self.close.shift(5)
        result = ABuDataFrameUtil.if_else_func(condition2, c3, c2)

        return result

    def alpha020(self):

        result = (self.close - self.close.shift(6)) / self.close.shift(6) * 100

        return result

    def alpha021(self):

        c1 = self.close.rolling(6).mean()
        c2 = pd.Series(range(1, 7), index=c1.index)
        beta_lis = []
        for i in range(len(c1)):

            c3 = c1[i:i+6]
            beta = ABuDataFrameUtil.linear_reg(c3, c2)[0]
            beta_lis.append(beta)

        return pd.Series(beta_lis, index=c1.index)

    def alpha022(self):

        c1 = (self.close - self.close.rolling(6).mean()) / self.close.rolling(6).mean()
        c2 = c1.shift(3)
        result = ABuDataFrameUtil.sma(c2 - c1, 12, 1)

        return result

    def alpha023(self):

        c1 = self.close.rolling(20).std()

        condition = self.close > self.close.shift(1)

        c2 = ABuDataFrameUtil.if_else_func(condition, c1, 0)
        c3 = ABuDataFrameUtil.if_else_func(~condition, c1, 0)

        c4 = ABuDataFrameUtil.sma(c2, 20, 1)
        c5 = ABuDataFrameUtil.sma(c3, 20, 1)

        result = c4 / (c5 + c4) * 100

        return result

    def alpha024(self):

        c1 = self.close - self.close.shift(5)

        result = ABuDataFrameUtil.sma(c1, 5, 1)

        return result

    def alpha025(self):

        c1 = self.volume / self.volume.rolling(20).mean()
        c2 = ABuDataFrameUtil.decay_linear(c1, 9)
        c3 = 1 - c2.rank()
        c4 = -1 * (self.close.diff(7).rank()) * c3
        c5 = 1 + self.ret.rolling(250).sum().rank()

        result = c4 * c5

        return result

    def alpha026(self):

        c1 = self.close.rolling(7).sum() / 7 - self.close
        c2 = self.vwap.rolling(230).corr(self.close.shift(5))

        return c1 + c2

    def alpha027(self):

        c1 = (self.close - self.close.shift(3)) / self.close.shift(3) * 100
        c2 = (self.close - self.close.shift(6)) / self.close.shift(3) * 100

        result = ABuDataFrameUtil.wma(c1 + c2, 12)

        return result

    def alpha028(self):

        c1 = self.close - self.low.rolling(9).min()
        c2 = self.high.rolling(9).max() - self.low.rolling(9).min()
        c3 = self.high.rolling(9).max() - self.low.rolling(9).max()

        result = 3 * ABuDataFrameUtil.sma(c1 / c2 * 100, 3, 1) - 2 * ABuDataFrameUtil.sma(ABuDataFrameUtil.sma(c1 / c3 *
                                                                                                               100, 3, 1
                                                                                                               ), 3, 1)

        return result

    def alpha029(self):

        result = (self.close - self.close.shift(6)) / self.close.shift(6) * self.volume

        return result

    def alpha030(self):

        pass

    def alpha031(self):

        c1 = self.close - self.close.rolling(12).mean()
        result = c1 / self.close.rolling(12).mean() * 100

        return result

    def alpha032(self):

        c1 = self.high.rank().rolling(3).corr(self.volume.rank())
        c2 = c1.rank().rolling(3).sum()

        return -c2

    def alpha033(self):

        c1 = -self.low.rolling(5).min() + self.low.rolling(5).min().shift(5)
        c2 = ((self.ret.rolling(240).sum() - self.ret.rolling(20).sum()) / 220).rank()
        c3 = ABuDataFrameUtil.rolling_rank(self.volume, 5)

        return c1 * c2 * c3

    def alpha034(self):

        return self.close.rolling(12).mean() / self.close

    def alpha035(self):

        c1 = ABuDataFrameUtil.decay_linear(self.open.diff(1), 15).rank()
        c2 = ABuDataFrameUtil.decay_linear(self.volume.rolling(17).corr(self.open * 0.65 + self.open * 0.35), 7).rank()

        return -1 * np.minimum(c1, c2)

    def alpha036(self):

        c1 = self.volume.rank().rolling(6).corr(self.vwap.rank())
        c2 = c1.rolling(2).sum()

        return c2.rank()

    def alpha037(self):

        c1 = self.open.rolling(5).sum() * self.ret.rolling(5).sum()
        c2 = c1.shift(10)

        return -((c1 - c2).rank())

    def alpha038(self):

        condition = self.high.rolling(20).sum() / 20 < self.high
        c1 = -(self.high.diff(2))

        return ABuDataFrameUtil.if_else_func(condition, c1, 0)

    def alpha039(self):

        c1 = ABuDataFrameUtil.decay_linear(self.close.diff(2), 8).rank()
        c2 = self.volume.rolling(180).mean().rolling(37).sum()
        c3 = (self.vwap * 0.3 + self.open * 0.7).rolling(14).corr(c2)

        c4 = ABuDataFrameUtil.decay_linear(c3, 12).rank()
        return (c1 - c4) * -1

    def alpha040(self):

        condition = self.close > self.close.shift(1)
        c1 = ABuDataFrameUtil.if_else_func(condition, self.volume, 0)
        c2 = ABuDataFrameUtil.if_else_func(~condition, self.volume, 0)

        result = c1.rolling(26).sum() / c2.rolling(26).sum() * 100

        return result

    def alpha041(self):

        c1 = np.maximum(self.vwap.diff(3), 5)
        result = c1.rank() * -1

        return result

    def alpha042(self):

        c1 = self.high.rolling(10).std().rank() * -1
        c2 = self.high.rolling(10).corr(self.volume)

        return c1 * c2

    def alpha043(self):

        condition1 = self.close > self.close.shift(1)
        condition2 = self.close < self.close.shift(1)

        c1 = ABuDataFrameUtil.if_else_func(condition2, -self.volume, 0)
        c2 = ABuDataFrameUtil.if_else_func(condition1, self.volume, c1)

        return c2.rolling(6).sum()

    def alpha044(self):

        c1 = self.low.rolling(7).self.volume.rolling(10).mean()
        c2 = ABuDataFrameUtil.rolling_rank(ABuDataFrameUtil.decay_linear(c1, 6), 4)

        c3 = ABuDataFrameUtil.rolling_rank(ABuDataFrameUtil.decay_linear(self.vwap.diff(3), 10), 15)

        return c2 + c3

    def alpha045(self):
        pass

