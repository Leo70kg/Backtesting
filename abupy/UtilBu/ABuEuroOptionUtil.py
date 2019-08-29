# -*- coding: utf-8 -*-
# Leo70kg
"""
欧式期权计算模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from ..UtilBu.ABuFileUtil import load_df_csv
from ..UtilBu.ABuDateUtil import date_str_to_int
from..CoreBu.ABuEnv import g_trade_date_list


def load_vol_df(symbol):
    """载入特定合约的波动率表"""
    file_name = r'C:\Users\BHQH-SERVER1\PycharmProjects\abu_backtest\abupy\RomDataBu\{:s}_vol.csv'.format(symbol.upper())
    df = load_df_csv(file_name)

    df['trade_date'] = df['trade_date'].apply(date_str_to_int)
    df.set_index("trade_date", inplace=True)

    return df


def get_vol_n_days_before(vol_df, today_date, n):
    """获取n天之前的波动率"""

    n_days_before_date = g_trade_date_list[g_trade_date_list.index(today_date) - n]
    try:
        vol = round(vol_df.at[n_days_before_date, 'EWMA_Vol'], 4)

    except KeyError as e:
        vol = 0.2

    return vol


def convert_day_to_year(t, date='trading'):
    """将天数转换成年"""

    if date == 'calendar':
        t_year = t / 365

    else:
        t_year = t / 252

    return t_year


def d_one(s, k, r, q, t, v, date='trading'):
    """计算bs模型中的d1"""
    t_year = convert_day_to_year(t, date)

    return (np.log(s / k) + (0.5 * v ** 2 + r - q) * t_year) / (v * np.sqrt(t_year))


# ----------------------------------------------------------------------
def bs_price(s, k, r, q, t, v, cp, date='trading'):
    """使用bs模型计算期权的价格"""
    t_year = convert_day_to_year(t, date)

    d1 = d_one(s, k, r, q, t, v, date)
    d2 = d1 - v * np.sqrt(t_year)
    price = cp * (s * np.exp(-q * t_year) * norm.cdf(cp * d1) - k * np.exp(-r * t_year) * norm.cdf(cp * d2))

    return price


# ----------------------------------------------------------------------
def bs_delta(s, k, r, q, t, v, cp, date='trading'):
    """使用bs模型计算期权的Delta"""

    t_year = convert_day_to_year(t, date)

    d1 = d_one(s, k, r, q, t, v, date)
    delta = cp * norm.cdf(cp * d1) * np.exp(-q * t_year)
    return delta


# ----------------------------------------------------------------------
def bs_gamma(s, k, r, q, t, v, cp, date='trading'):
    """使用bs模型计算期权的Gamma"""

    t_year = convert_day_to_year(t, date)

    d1 = d_one(s, k, r, q, t, v, date)
    gamma = norm.pdf(d1) / (s * v * np.sqrt(t_year)) * np.exp(-q * t_year)

    return gamma


# ----------------------------------------------------------------------
def bs_vega(s, k, r, q, t, v, cp, date='trading'):
    """使用bs模型计算期权的Vega"""
    t_year = convert_day_to_year(t, date)

    d1 = d_one(s, k, r, q, t, v, date)
    vega = s * norm.pdf(d1) * np.sqrt(t_year) * np.exp(-q * t_year)

    return vega


# ----------------------------------------------------------------------
def bs_theta(s, k, r, q, t, v, cp, date='trading'):
    """使用bs模型计算期权的Theta"""
    t_year = convert_day_to_year(t, date)

    d1 = d_one(s, k, r, q, t, v, date)
    d2 = d1 - v * np.sqrt(t_year)

    theta = -(s * v * norm.pdf(d1) * np.exp(-q * t_year)) / (2 * np.sqrt(t_year)) - \
        cp * r * k * np.exp(-r * t_year) * norm.cdf(cp * d2) + \
        cp * q * s * norm.cdf(cp * d1) * np.exp(-q * t_year)

    return theta


def bs_iv(s, k, r, q, t, cp, price, date='trading'):
    """使用bs模型计算期权的隐含波动率"""
    def func(sigma):
        return bs_price(s, k, r, q, t, sigma, cp, date) - price

    iv = brentq(func, 0.001, 1.5)
    return iv
