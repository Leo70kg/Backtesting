# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..UtilBu.ABuKlineUtil import min_kline, day_kline
from ..UtilBu.ABuStrUtil import get_num_from_str, get_letters
from ..CoreBu.ABuEnv import g_futures_kline_num_dict
from ..UtilBu.ABuDateUtil import datetime_trans_to_resampled as trans


class AbuDataHandler(object):

    def __init__(self, kl_pd, freq):

        self.kl_pd_dict = dict({freq.upper(): kl_pd})

    @classmethod
    def get_kline_num(cls, kl_df, freq):
        num = g_futures_kline_num_dict[freq][get_letters(kl_df.name)]
        return num

    @classmethod
    def handle_kline(cls, kl_df, freq, symbol):
        """
        合成n分钟k线方法
        :param kl_df: 原始一分钟行情
        :param freq: str格式，‘15m’
        :param symbol: 合约代码，‘RU1901'
        :return:
        """
        day_or_minute = get_letters(freq)
        fq = get_num_from_str(freq)

        if day_or_minute == 'D':
            kline_num = fq

            return day_kline(symbol, kl_df, fq), kline_num

        else:
            column_name = freq + '_resampled_datetime'

            freq_kl_df = min_kline(symbol, kl_df, fq)
            kl_df[column_name] = list(map(lambda datetime, date_ind: trans(str(datetime), date_ind, fq), kl_df.datetime,
                                          kl_df.date))

            kline_num = g_futures_kline_num_dict[freq][get_letters(kl_df.name)] if freq in g_futures_kline_num_dict \
                else None

            return freq_kl_df, kline_num
