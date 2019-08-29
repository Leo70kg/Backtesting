# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..CoreBu.ABuEnv import MysqlCfg
from ..MarketBu.ABuDataBase import StockBaseMarket, SupportMixin
from ..MarketBu.ABuDataParser import MySqlParser
from ..UtilBu.ABuDateUtil import get_start
from sqlalchemy import create_engine
import pandas as pd
import math


class MysqlApi(StockBaseMarket, SupportMixin):

    def __init__(self, symbol):
        """
        :param symbol: Symbol类型对象
        """
        super(MysqlApi, self).__init__(symbol)

        self.data_parser_cls = MySqlParser

    def kline(self, n_folds=2, start=None, end=None):
        """日k线接口"""

        engine = create_engine("{:s}://{:s}:{:s}@{:s}/{:s}?charset=utf8".format(MysqlCfg.engine.value,
                                                                                MysqlCfg.user.value,
                                                                                MysqlCfg.password.value,
                                                                                MysqlCfg.ip.value,
                                                                                MysqlCfg.database.value))

        if start:
            sql = """select * from {:s} where trade_date >= '{:s}' and trade_date <= '{:s}'""".format(
                    self._symbol.symbol_code, start, end)

        else:
            num = math.floor(n_folds * 252)
            sql = """select * from {:s} order by id desc limit {:d}""".format(self._symbol.symbol_code, num)

        kl_df = pd.read_sql(sql, engine, index_col='trade_date').sort_values(by='id')

        return self.data_parser_cls(self._symbol, kl_df).df

    def minute(self, n_folds=2, start=None, end=None):
        """分钟k线接口"""

        engine = create_engine("{:s}://{:s}:{:s}@{:s}/{:s}?charset=utf8".format(MysqlCfg.engine.value,
                                                                                MysqlCfg.user.value,
                                                                                MysqlCfg.password.value,
                                                                                MysqlCfg.ip.value,
                                                                                MysqlCfg.database1.value))

        if not start:
            start, end = get_start(n_folds, start=start, end=end)

        sql = """select * from {:s} where trade_time >= '{:s} 09:00:00' and trade_time <= '{:s} 15:00:00' """.format(
                                                                                self._symbol.symbol_code, start, end)

        kl_df = pd.read_sql(sql, engine, index_col='trade_time').sort_values(by='id')

        return self.data_parser_cls(self._symbol, kl_df).df
