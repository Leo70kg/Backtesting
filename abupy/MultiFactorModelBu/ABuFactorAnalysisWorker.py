# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from . import ABuFactorUtil
import numpy as np
import pandas as pd


def time_series_analysis(data, factor_name_func, window):
    """
    对因子时间序列与收益率进行时序回归分析
    :param data: 时间序列，dataFrame或者Panel对象
    :param factor_name_func: dict格式，key为因子名称，形式为str，
                            value为因子计算函数和所需参数，形式为tuple，参数可以为单值或list,无参数的话为None
                            要求输出列表或Series，lis格式，针对同时计算多个因子值
    :param window: 用于回归的数据集长短，int格式
    :return:
    """
    if isinstance(data, pd.DataFrame):

        factor_df = ABuFactorUtil.calc_df_factor(data, factor_name_func)
        x = factor_df[factor_name_func.keys()]
        y = factor_df['log_return']

        return ABuFactorUtil._time_series_df_regression(x, y, window)

    elif isinstance(data, pd.Panel):
        factor_panel = ABuFactorUtil.calc_panel_factor(data, factor_name_func)

        return ABuFactorUtil._time_series_panel_regression(factor_panel, factor_name_func.keys(), window)


def cross_section_analysis(data, factor_name_func, date_str):
    """
    对因子截面数据与收益率进行截面分析
    :param data: 时间序列，dataFrame或者Panel对象
    :param factor_name_func: dict格式，key为因子名称，形式为str，
                            value为因子计算函数和所需参数，形式为tuple，参数可以为单值或list,无参数的话为None
                            要求输出列表或Series，lis格式，针对同时计算多个因子值
    :param date_str: 日期，可以是str或者lis对象，针对时间序列data选取具体某一天的截面数据
    :return:
    """
    def single_period_analysis(kl_df, factor_dict):
        """计算单期因子回归"""
        x = kl_df[factor_dict.keys()]
        y = kl_df['post_log_return']

        return ABuFactorUtil._cross_section_regression(x, y)

    factor_df = ABuFactorUtil.calc_panel_factor(data, factor_name_func)

    if isinstance(date_str, (str, unicode)):
        reg_array = np.zeros([1, 1])
        df = ABuFactorUtil._convert_cs_df(factor_df, date_str)
        reg = single_period_analysis(df, factor_name_func)
        reg_array[0] = reg.values()

        return pd.DataFrame(reg_array, index=date_str, columns=reg.keys())

    elif isinstance(date_str, list):
        reg_array = np.zeros([len(date_str), 1])

        for i in xrange(len(date_str)):
            df = ABuFactorUtil._convert_cs_df(factor_df, date_str[i])

            try:
                reg = single_period_analysis(df, factor_name_func)
            except KeyError:
                reg_array[i] = np.nan

            reg_array[i] = reg.values()

        return pd.DataFrame(reg_array, index=date_str, columns=reg.keys())


def factor_ic(data, factor_name_func, date_str, rank_ic=False):
    """
    对多个因子分别计算IC值
    :param data: 时间序列，dataFrame或者Panel对象
    :param factor_name_func:
    :param date_str:
    :param rank_ic: 是否用秩相关系数计算ic，默认为否
    :return: dict对象
    """
    factor_df = ABuFactorUtil.calc_panel_factor(data, factor_name_func)

    def single_period_ic(kl_df, factor_dict):
        """计算单期因子IC"""
        dic = {}
        if rank_ic:
            calc_ic_func = ABuFactorUtil._calc_rank_ic
        else:
            calc_ic_func = ABuFactorUtil._calc_ic

        for factor_name in factor_dict.keys():
            x = kl_df[factor_name]
            y = kl_df['post_log_return']
            dic[factor_name] = calc_ic_func(x, y)

        return dic

    if isinstance(date_str, (str, unicode)):
        ic_array = np.zeros([1, len(factor_name_func)])

        df = ABuFactorUtil._convert_cs_df(factor_df, date_str)
        ic = single_period_ic(df, factor_name_func)
        ic_array[0] = ic.values()

        return pd.DataFrame(ic_array, index=date_str, columns=ic.keys())

    elif isinstance(date_str, list):
        ic_array = np.zeros([len(date_str), len(factor_name_func)])
        for i in xrange(len(date_str)):
            df = ABuFactorUtil._convert_cs_df(factor_df, date_str[i])
            ic = single_period_ic(df, factor_name_func)
            ic_array[i] = ic.values()

        return pd.DataFrame(ic_array, index=date_str, columns=ic.keys())

