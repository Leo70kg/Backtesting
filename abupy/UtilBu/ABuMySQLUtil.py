#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/17 0017 22:18
# @Author  : Leo70kg

"""
MySQL数据库处理模块
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import re

from ..CoreBu.ABuEnv import MysqlCfg


def get_dominant_contract(choice_symbols, start, end):
    """
    根据期货主力合约列表，以及起始截止日期，获取具体期货月合约
    :param choice_symbols: 期货主力合约列表
    :param start: 起始日期，datetime.date格式
    :param end: 终止日期， datetime.date格式
    :return: 月合约列表，list格式
    """

    code_lis = [re.search('\D+', code.upper()).group()+'9999' for code in choice_symbols]

    engine = create_engine("{:s}://{:s}:{:s}@{:s}/{:s}?charset=utf8".format(MysqlCfg.engine.value,
                                                                            MysqlCfg.user.value,
                                                                            MysqlCfg.password.value,
                                                                            MysqlCfg.ip.value,
                                                                            MysqlCfg.database.value))

    sql = "select * from hiscode"

    df = pd.read_sql(sql, engine, index_col='trade_date')

    df = df[(df.index <= end) & (df.index >= start)][code_lis]

    symbols = []
    for symbol in code_lis:
        if symbol == 'FU9999':
            pass

        symbol_df = df[symbol].drop_duplicates()
        temp = symbol_df.replace('', np.nan)
        temp = temp.dropna()

        symbols += temp.values.tolist()

    symbols = [symbol.split('.')[0] for symbol in symbols]

    return symbols

