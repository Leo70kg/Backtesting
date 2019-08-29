# -*- coding: utf-8 -*-
# Leo70kg
"""
    合成k线工具模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd

from ..CoreBu import ABuEnv
from ..UtilBu import ABuDateUtil
from ..UtilBu.ABuStrUtil import get_letters


# TODO 提高效率
def min_kline(symbol, kl_df, freq=5):
    """
    根据原始的一分钟行情dataframe，制定时间频率，e.g.5分钟，15分钟合成对应的分钟行情dataframe
    :param symbol: 行情代码
    :param kl_df: 原始dataframe
    :param freq: 频率，int格式
    :return: 合成后的行情dataframe
    """

    if freq == 1:
        kl_df.name = symbol
        return kl_df

    freq = '{:d}T'.format(freq)
    new_df = pd.DataFrame(columns=kl_df.columns)
    new_df.open = kl_df.open.resample(freq, label='right', closed='right').apply(get_first)
    new_df.close = kl_df.close.resample(freq, label='right', closed='right').apply(get_last)
    new_df.high = kl_df.high.resample(freq, label='right', closed='right').max()
    new_df.low = kl_df.low.resample(freq, label='right', closed='right').min()

    new_df.volume = kl_df.volume.resample(freq, label='right', closed='right').sum()
    new_df.amount = kl_df.amount.resample(freq, label='right', closed='right').sum()
    new_df.date = kl_df.date.resample(freq, label='right', closed='right').apply(get_first)

    multiplier = ABuEnv.g_futures_cn_info_dict['contract_multiplier'][get_letters(symbol)]
    new_df.vwap = new_df.amount * 1000000 / (new_df.volume * multiplier)
    new_df.log_return = kl_df.log_return.resample(freq, label='right', closed='right').sum()

    # dates_fmt = list(map(lambda date: str(date), new_df.index))
    # dates = list(map(lambda date: ABuDateUtil.date_str_to_int(date), dates_fmt))
    datetimes = new_df.index

    # new_df['date'] = dates
    new_df['datetime'] = datetimes
    # new_df['date_week'] = new_df['date'].apply(lambda x: ABuDateUtil.week_of_date(str(x), '%Y%m%d'))
    new_df['timestamp'] = list(map(lambda date: ABuDateUtil.time_to_timestamp(date), new_df.index))
    new_df['pre_close'] = new_df['close'].shift(1)
    new_df['pre_close'].fillna(new_df['open'], axis=0, inplace=True)

    new_df.dropna(subset=['open', 'close', 'high', 'low'], inplace=True)
    new_df['date'] = new_df['date'].astype(int)
    new_df['date_week'] = new_df['date'].apply(lambda x: ABuDateUtil.week_of_date(str(x), '%Y%m%d'))
    new_df['p_change'] = (new_df['close'].diff(1) / new_df['close'].shift(1))
    new_df['key'] = list(range(0, len(new_df)))

    new_df['revised_datetime'] = list(map(lambda datetime, date_ind: ABuDateUtil.resampled_df_revise(str(datetime),
                                                                                                     date_ind),
                                          new_df.datetime, new_df.date))

    new_df['datetime'] = new_df['datetime'].astype(str)
    new_df['revised_datetime'] = new_df['revised_datetime'].astype(str)

    new_df.name = symbol

    return new_df


def day_kline(symbol, kl_df, freq=1):
    """
    根据原始的一分钟行情dataframe，合成日线行情dataframe 制定时间频率，e.g.5分钟，15分钟合成对应的分钟行情dataframe
    :param symbol: 行情代码
    :param kl_df: 原始dataframe
    :param freq: 频率，int格式
    :return: 合成后的行情dataframe
    """

    index_lis = kl_df.index
    new_index_lis = index_lis + pd.Timedelta(hours=3)

    new_kl_df = kl_df.set_index(new_index_lis)

    freq = '{:d}B'.format(freq)
    new_df = pd.DataFrame(columns=new_kl_df.columns)
    new_df.open = new_kl_df.open.resample(freq, label='right', closed='right').apply(get_first)
    new_df.close = new_kl_df.close.resample(freq, label='right', closed='right').apply(get_last)
    new_df.high = new_kl_df.high.resample(freq, label='right', closed='right').max()
    new_df.low = new_kl_df.low.resample(freq, label='right', closed='right').min()

    new_df.volume = new_kl_df.volume.resample(freq, label='right', closed='right').sum()
    new_df.amount = new_kl_df.amount.resample(freq, label='right', closed='right').sum()

    multiplier = ABuEnv.g_futures_cn_info_dict['contract_multiplier'][get_letters(symbol)]
    new_df.vwap = new_kl_df.amount * 1000000 / (new_kl_df.volume * multiplier)
    new_df.log_return = new_kl_df.log_return.resample(freq, label='right', closed='right').sum()

    dates_fmt = list(map(lambda date: str(date), new_df.index))
    dates = list(map(lambda date: ABuDateUtil.date_str_to_int(date), dates_fmt))
    datetimes = new_df.index

    new_df['date'] = dates
    new_df['datetime'] = datetimes
    new_df['date_week'] = new_df['date'].apply(lambda x: ABuDateUtil.week_of_date(str(x), '%Y%m%d'))
    new_df['timestamp'] = list(map(lambda date: ABuDateUtil.time_to_timestamp(date), new_df.index))
    new_df['pre_close'] = new_df['close'].shift(1)
    new_df['pre_close'].fillna(new_df['open'], axis=0, inplace=True)

    new_df.dropna(subset=['open', 'close', 'high', 'low'], inplace=True)
    new_df['p_change'] = (new_df['close'].diff(1) / new_df['close'].shift(1))
    new_df['key'] = list(range(0, len(new_df)))

    new_df['datetime'] = new_df['datetime'].astype(str)

    new_df.name = symbol

    return new_df


def get_last(array_like):

    if array_like.empty:
        return np.nan
    else:
        return array_like[-1]


def get_first(array_like):
    if array_like.empty:
        return np.nan
    else:
        return array_like[0]