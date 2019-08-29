# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .ABuFactorUtil import sma
import numpy as np


# noinspection PyUnusedLocal
def _calc_tr(kl_df, *args):
    """
    计算真实波幅
    :param kl_df: 时间序列，dataFrame格式
    :return: ndarray或者series格式
    """
    high = kl_df['high'].values
    low = kl_df['low'].values
    close = kl_df['close'].values

    import talib

    tr = talib.TRANGE(high, low, close)

    return tr


# noinspection PyUnusedLocal
def _calc_oi_st(kl_df, *args):
    """
    计算持仓量与注册仓单的比值
    :param kl_df: 时间序列，dataFrame格式
    :return: ndarray或者series格式
    """
    oi = kl_df['oi']
    st = kl_df['ST_STOCK']

    return oi / st


# noinspection PyUnusedLocal
def _calc_return_ratio(kl_df, *args):
    """
    计算N日内的收益率与N日内每日收益率绝对值之和的比值
    :param kl_df: 时间序列，dataFrame格式
    :return: ndarray或者series格式
    """

    log_ret = kl_df['log_return']
    abs_log_ret = np.abs(log_ret)
    n = args[0]

    nd_log_ret = log_ret.rolling(window=n).sum()
    nd_abs_log_ret = abs_log_ret.rolling(window=n).sum()

    return nd_log_ret / nd_abs_log_ret


def _calc_adx(kl_df, *args):
    """
    计算adx平均趋向指数，ADX指数是反映趋向变动的程度，而不是方向的本身
    :param kl_df:
    :param args:
    :return:
    """
    high = kl_df['high'].values
    low = kl_df['low'].values
    close = kl_df['close'].values

    import talib

    adx = talib.ADX(high, low, close)

    return adx


def _calc_factor1(kl_df, *args):

    close = kl_df['close']
    n = args[0]

    delay_close = close.shift(n)
    result = (close - delay_close) / delay_close

    return result


# noinspection PyUnusedLocal
def _calc_factor2(kl_df, *args):

    high = kl_df['high']
    low = kl_df['low']
    vwap = kl_df['vwap']

    return (high * low) ** 0.5 - vwap


def _calc_factor29(kl_df, *args):

    close = kl_df['close']
    volume = kl_df['volume']

    n = args[0]
    delay_close = close.shift(n)

    result = (close - delay_close) / delay_close * volume

    return result


def _calc_factor58(kl_df, *args):

    close = kl_df['close']
    n = args[0][0]
    delay_close = close.shift(n)

    condition = (close > delay_close).replace(False, np.nan)

    result = condition.rolling(window=args[0][1]).count() / args[0][1]

    return result


# noinspection PyUnusedLocal
def _calc_factor109(kl_df, *args):

    high = kl_df['high']
    low = kl_df['low']

    c = sma(high - low, 10, 2)
    return c / sma(c, 10, 2)

