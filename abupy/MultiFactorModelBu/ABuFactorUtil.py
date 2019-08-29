# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..UtilBu.ABuDateUtil import str_to_date_fast
from ..UtilBu.ABuRegUtil import regress_multi_xy

import pandas as pd
import numpy as np


def calc_df_factor(kl_df, factor_name_func):
    """
    在已经取得的期货品种行情信息dataFrame中计算因子值，
    并添加到已有的dataFrame中
    :param kl_df:   期货合约的时序，dataFrame格式
    :param factor_name_func:    dict格式，key为因子名称，形式为str，
                                value为因子计算函数和所需参数，形式为tuple，参数可以为单值或list,无参数的话为None
                                要求输出列表或Series，lis格式，针对同时计算多个因子值
    :return:    添加计算后因子值的时序
    """
    for (factor_name, tup) in factor_name_func.items():
        func = tup[0]
        args = tup[1]

        result = func(kl_df, args)
        kl_df[factor_name] = result

    return kl_df.dropna()


def calc_panel_factor(kl_panel, factor_name_func):
    """
    calc_df_factor拓展，针对pandas.panel格式
    :param kl_panel: panel格式
    :param factor_name_func: 同calc_df_factor
    :return:
    """
    dic = {}
    for i in xrange(len(kl_panel)):
        df = calc_df_factor(kl_panel.ix[i], factor_name_func)
        key = kl_panel.items[i]
        dic[key] = df

    return pd.Panel(dic)


def normalize_factor(ft_df):
    """
    对因子序列进行标准化
    :param ft_df: 因子序列，dataFrame或Series格式
    :return: 标准化后的因子序列
    """

    return (ft_df - ft_df.mean()) / ft_df.std()


def _dict_add_element(dic, key, value):
    """
    在字典中添加键值，供内部调用
    :param dic:
    :param key:
    :param value:
    :return:
    """
    dic[key] = value

    return dic


def _convert_cs_df(ts_df, date_str):
    """
    将多个标的的时间序列数据选取某一日期的数据构成面板数据
    :param ts_df: 时间序列集合，panel格式
    :param date_str: 具体日期，str格式，形如‘2018-10-10’
    :return:
    """

    date = str_to_date_fast(date_str)
    ft_df = pd.DataFrame()

    for i in xrange(len(ts_df)):
        ft_df[ts_df.items[i]] = ts_df.ix[i].loc[date]

    return ft_df.T


def _cross_section_regression(cs_df, ret_df):
    """
    对多个因子进行截面回归
    :param cs_df: 因子截面数据，dataFrame格式
    :param ret_df: 每日收益率数据，Series格式
    :return:
    """
    reg = regress_multi_xy(cs_df, ret_df)

    # return {'R^2: ': reg.score(cs_df, ret_df), 'coef: ': reg.coef_, 'intercept: ': reg.intercept_}
    return {'R^2: ': reg.score(cs_df, ret_df)}


def _time_series_df_regression(ft_df, ret_df, window):
    """
    对多个因子进行时序回归
    :param ft_df: 因子时间序列，dataFrame格式
    :param ret_df: 每日收益率数据，Series格式
    :param window: 用于回归的数据集长短，int格式
    :return:
    """
    reg = regress_multi_xy(ft_df[-window:], ret_df[-window:])
    return {'R^2: ': reg.score(ft_df, ret_df), 'coef: ': reg.coef_, 'intercept: ': reg.intercept_}


def _time_series_panel_regression(ft_panel, factor_name, window):
    """
    在面板中分别对每个dataFrame进行多因子时序回归
    :param ft_panel: 总面板数据，panel格式
    :param factor_name: 因子名称，lis格式
    :return: 回归模型结果，lis格式
    """
    reg_dict = {}
    for i in xrange(len(ft_panel)):
        df = ft_panel.ix[i]
        ft_df = df[factor_name]
        ret_df = df['log_return']

        reg = _time_series_df_regression(ft_df, ret_df, window)
        reg_dict[ft_panel.items[i]] = reg

    return reg_dict


def _calc_ic(factor_series, ret_series):
    """
    计算单因子IC值
    :param factor_series: 当期因子截面，Series对象
    :param ret_series: 下期收益率截面，Series对象
    :return: int对象
    """
    if isinstance(factor_series, pd.DataFrame):
        factor_series = factor_series

    return factor_series.corr(ret_series)


def _calc_rank_ic(factor_series, ret_series):
    """
    计算单因子RANK IC值
    :param factor_series:
    :param ret_series:
    :return:
    """
    if isinstance(factor_series, pd.DataFrame):
        factor_series = factor_series

    return factor_series.corr(ret_series, method='spearman')


def calc_ic_ir(ic_series):
    """
    因子的IR(信息比)值为因子IC的均值和因子IC的标准差的比值，IR值越高越好
    :param ic_series: IC值序列
    :return:
    """
    return ic_series.mean() / ic_series.std()


def sma(s, n, m):
    """计算SMA均线，n为周期，m为权重，s为时间序列"""

    i = 0
    while s.iloc[i] is np.nan:
        i = i + 1

    count_lis = []
    for j in range(i, len(s)):

        if j+i < n-1+i:
            count_lis.append(np.nan)
        else:
            s1 = s[j-n+i+1:j+i+1]
            count = s1.iloc[0]

            for k in range(len(s1)):

                count = (s1.iloc[k] * m + count * (n - m)) / n

            count_lis.append(count)

    return pd.Series(count_lis, index=s.index)