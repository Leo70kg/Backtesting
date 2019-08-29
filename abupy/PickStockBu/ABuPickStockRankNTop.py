# -*- coding: utf-8 -*-
# Leo70kg
"""
    选股因子：根据价格等计算技术指标，根据排序选择靠前的标的
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import os, re, copy

from .ABuPickStockBase import AbuPickStockBase, reversed_result
from ..CoreBu.ABuEnv import EMarketDataSplitMode
from ..MarketBu import ABuSymbolPd
from ..TradeBu import AbuBenchmark
from ..UtilBu import ABuDateUtil
from ..CoreBu import ABuEnv


_rom_dir = ABuEnv.g_project_rom_data_dir
"""国内期货symbol文件，文件定期重新爬取，更新"""
_futures_cn_date = os.path.join(_rom_dir, 'futures_cn_date.csv')
_futures_cn_hiscode = os.path.join(_rom_dir, 'futures_cn_hiscode.csv')


class AbuPickStockRankNTop(AbuPickStockBase):
    """根据一段时间内的技术指标选取top N个"""

    def _init_self(self, **kwargs):
        """通过kwargs设置选股条件，配置因子参数"""
        # 选股参数symbol_pool：进行涨幅比较的top n个symbol
        self.symbol_pool = kwargs.pop('symbol_pool', [])
        # 选股参数n_top：选取前n_top个symbol, 默认3
        self.n_top = kwargs.pop('n_top', 3)
        # 选股参数direction_top：选取前n_top个的方向，即选择涨的多的，还是选择跌的多的
        self.direction_top = kwargs.pop('direction_top', 1)
        # 获取主力合约信息
        self.futures_cn_df = pd.read_csv(_futures_cn_date, index_col=0)
        # 获取主力合约具体月合约
        self.futures_cn_hiscode = pd.read_csv(_futures_cn_hiscode, index_col=0)

        # 获取并保存具体合约的起始日期
        self.futures_date = {}

        # if len(self.symbol_pool) != 0 and ABuEnv.g_dominant_contract:
        #
        #     for symbol in self.symbol_pool:
        #
        #         start_date_int = ABuDateUtil.date_str_to_int(self.futures_cn_df[self.futures_cn_df['symbol'] ==
        #                                                                         symbol].start_date.values[0])
        #
        #         end_date = self.futures_cn_df[self.futures_cn_df['symbol'] == symbol].end_date.values[0]
        #         end_date_int = ABuDateUtil.date_str_to_int(end_date) if end_date is not np.NAN else np.inf
        #
        #         self.futures_date[symbol] = [start_date_int, end_date_int]

    @reversed_result
    def fit_pick(self, kl_pd, target_symbol):
        """开始根据参数进行选股"""
        if len(self.symbol_pool) == 0:
            # 如果没有传递任何参照序列symbol，择默认为选中
            return True

        if ABuEnv.g_dominant_contract:

            code_lis = [re.search('\D+', code.upper()).group() + '9999' for code in self.symbol_pool]

            futures_symbol_pool = self.futures_cn_hiscode[code_lis].loc[ABuDateUtil.timestamp_to_str(kl_pd.index[-1])].tolist()

            s_symbol_pool = []
            for future_symbol in futures_symbol_pool:
                if future_symbol is np.nan:
                    pass
                else:
                    symbol = future_symbol.split('.')[0]
                    s_symbol_pool.append(symbol)

            # futures_symbol_pool = []
            # date_int = ABuDateUtil.date_str_to_int(ABuDateUtil.timestamp_to_str(kl_pd.index[-1]))
            #
            # for symbol, date_lis in self.futures_date.items():
            #     if symbol == target_symbol:
            #         if date_int < date_lis[0] or date_int > date_lis[1]:
            #             return False
            #
            #     if date_lis[0] <= date_int <= date_lis[1]:
            #         futures_symbol_pool.append(symbol)

        symbol_pool = s_symbol_pool if ABuEnv.g_dominant_contract else self.symbol_pool
        cmp_top_array = []
        kl_pd.name = target_symbol
        # AbuBenchmark直接传递一个kl
        benchmark = AbuBenchmark(benchmark_kl_pd=kl_pd)
        # print('target_symbol: ', target_symbol)
        # print(kl_pd)
        kl_df_dict = {}
        dsi_list = []
        rsi_list = []
        for symbol in symbol_pool:
            if symbol != target_symbol:
                # 使用benchmark模式进行获取
                kl = ABuSymbolPd.make_kl_df(symbol, data_mode=EMarketDataSplitMode.E_DATA_SPLIT_UNDO,
                                            benchmark=benchmark)

            else:
                kl = kl_pd
            try:
                dsi_list.append(kl.dsi.iloc[-1])
                rsi_list.append(kl.rsi.iloc[-1])
                kl_df_dict[symbol] = kl

            except BaseException as msg:
                print(msg)

        for symbol in symbol_pool:

            if symbol != target_symbol:
                # 使用benchmark模式进行获取
                kl = kl_df_dict[symbol]

                if kl is not None:
                    # 需要获取实际交易日数量，避免停盘等错误信号
                    cmp_top_array.append((kl.dsi.iloc[-1] - np.mean(dsi_list)) / np.std(dsi_list, ddof=1) +
                                         (kl.rsi.iloc[-1] - np.mean(rsi_list)) / np.std(rsi_list, ddof=1))

        if self.n_top > len(cmp_top_array):
            # 如果结果序列不足n_top个，直接认为选中
            return True

        # 与选股方向相乘，即结果只去top
        cmp_top_array = np.array(cmp_top_array) * self.direction_top
        # 计算本源的周期内指标值
        target_change = ((kl_pd.dsi.iloc[-1] - np.mean(dsi_list)) / np.std(dsi_list, ddof=1) +
                         (kl_pd.rsi.iloc[-1] - np.mean(rsi_list)) / np.std(rsi_list, ddof=1)) * self.direction_top

        # sort排序小－》大, 非inplace
        cmp_top_array.sort()
        # [::-1]大－》小
        # noinspection PyTypeChecker

        # f = open(r'C:\Users\BHRS-ZY-PC\Desktop\out.txt', 'a')
        # f.write(
        #     '\n {:d} {:s} {:f} {:f}'.format(ABuDateUtil.date_str_to_int(ABuDateUtil.timestamp_to_str(kl_pd.index[-1])),
        #                                     target_symbol, target_change, cmp_top_array[::-1][self.n_top - 1]))
        # f.close()
        if target_change > cmp_top_array[::-1][self.n_top - 1]:
            # 如果比排序后的第self.n_top位置上的大就认为选中
            return True
        return False

    def fit_first_choice(self, pick_worker, choice_symbols, *args, **kwargs):
        raise NotImplementedError('AbuPickStockNTop fit_first_choice unsupported now!')