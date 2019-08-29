# -*- encoding:utf-8 -*-
"""
    资金模块，不区分美元，人民币等类型，做美股交易默认当作美元，a股默认当作人民币
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import logging

import numpy as np
import pandas as pd

from ..UtilBu.ABuProgress import AbuProgress
from ..UtilBu import ABuDateUtil
from ..TradeBu.ABuOrder import AbuOrder
from ..TradeBu.ABuCommission import AbuCommission, query_commission, query_deposit
from ..CoreBu.ABuBase import PickleStateMixin
from ..UtilBu.ABuKlineUtil import day_kline


class AbuCapitalFutureDailyTest(PickleStateMixin):
    """资金类（每日统计），针对期货回测"""

    def __init__(self, init_cash, benchmark, user_commission_dict=None):
        """
        :param init_cash: 初始资金值，注意这里不区分美元，人民币等类型，做美股交易默认当作美元，a股默认当作人民币，int
        :param benchmark: 资金回测时间标尺，做为资金类表格时间范围确定使用，AbuBenchmark实例对象
        :param user_commission_dict: dict对象，可自定义交易手续费计算方法，详情查看AbuCommission
        """
        self.read_cash = init_cash

        kl_pd = benchmark.kl_pd
        if kl_pd is None:
            # 要求基准必须有数据
            raise ValueError('CapitalClass init klPd is None')

        # 根据基准时间序列，制作相同的时序资金对象capital_pd(pd.DataFrame对象)
        datetime_format_list = list(map(lambda date: pd.to_datetime(ABuDateUtil.fmt_date(date)),
                                        np.unique(kl_pd.date.values)))
        length = len(datetime_format_list)

        self.capital_pd = pd.DataFrame(
            {
                'cash_blance': np.NAN * length,
                'deposits_blance': np.NAN * length,
                'profits_blance': np.zeros(length),
                'date': np.unique(kl_pd.date.values)
            },
            index=datetime_format_list)

        self.capital_pd['date'] = self.capital_pd['date'].astype(int)

        # cash_blance除了第一个其它都是nan
        self.capital_pd.at[self.capital_pd.index[0], 'cash_blance'] = self.read_cash

        # 构造交易手续费对象AbuCommission，如果user自定义手续费计算方法，通过user_commission_dict传入
        self.commission = AbuCommission(user_commission_dict)

        self.sum_commission = 0

        self.cash_balance = self.read_cash

        # self.option_info = OrderedDict()

    def __str__(self):
        """打印对象显示：capital_pd.info commission_df.info"""
        return 'capital_pd:\n{}\ncommission_pd:\n{}'.format(self.capital_pd.info(),
                                                            self.commission.commission_df.info())

    __repr__ = __str__

    def __len__(self):
        """对象长度：时序资金对象capital_pd的行数，即self.capital_pd.shape[0]"""
        return self.capital_pd.shape[0]

    def init_k_line(self, a_symbol):
        """
        每一个交易对象在时序资金对象capital_pd上都添加对应的call keep（买涨持仓量），call worth（买涨总价值），
        put keep（买跌持仓量），put worth（买跌总价值）
        :param a_symbol: symbol str对象
        """
        columns_list = self.capital_pd.columns.tolist()

        # 买涨持仓量
        call_keep = '_call_keep'
        if columns_list.count(a_symbol + call_keep) == 0:
            self.capital_pd[a_symbol + call_keep] = np.NAN * \
                                                    self.capital_pd.shape[0]
        # 买跌持仓量
        put_keep = '_put_keep'
        if columns_list.count(a_symbol + put_keep) == 0:
            self.capital_pd[a_symbol + put_keep] = np.NAN * \
                                                   self.capital_pd.shape[0]
        # 买涨总价值
        call_worth = '_call_worth'
        if columns_list.count(a_symbol + call_worth) == 0:
            self.capital_pd[a_symbol + call_worth] = np.NAN * \
                                                     self.capital_pd.shape[0]

        # 买跌总价值
        put_worth = '_put_worth'
        if columns_list.count(a_symbol + put_worth) == 0:
            self.capital_pd[a_symbol + put_worth] = np.NAN * \
                                                    self.capital_pd.shape[0]

        # 买涨保证金
        call_deposit = '_call_deposit'
        if columns_list.count(a_symbol + call_deposit) == 0:
            self.capital_pd[a_symbol + call_deposit] = np.NAN * \
                                                    self.capital_pd.shape[0]

        # 买跌保证金
        put_deposit = '_put_deposit'
        if columns_list.count(a_symbol + put_deposit) == 0:
            self.capital_pd[a_symbol + put_deposit] = np.NAN * \
                                                    self.capital_pd.shape[0]

        # 买涨持仓均价
        call_holding_price = '_call_holding_price'
        if columns_list.count(a_symbol + call_holding_price) == 0:
            self.capital_pd[a_symbol + call_holding_price] = np.NAN * \
                                                             self.capital_pd.shape[0]

        # 买跌持仓均价
        put_holding_price = '_put_holding_price'
        if columns_list.count(a_symbol + put_holding_price) == 0:
            self.capital_pd[a_symbol + put_holding_price] = np.NAN * \
                                                            self.capital_pd.shape[0]

        # 买涨浮动盈亏
        call_holding_profit = '_call_holding_profit'
        if columns_list.count(a_symbol + call_holding_profit) == 0:
            self.capital_pd[a_symbol + call_holding_profit] = np.NAN * \
                                                            self.capital_pd.shape[0]

        # 买跌浮动盈亏
        put_holding_profit = '_put_holding_profit'
        if columns_list.count(a_symbol + put_holding_profit) == 0:
            self.capital_pd[a_symbol + put_holding_profit] = np.NAN * \
                                                            self.capital_pd.shape[0]

        # 买涨累计平仓盈亏
        call_clear_profit = '_call_clear_profit'
        if columns_list.count(a_symbol + call_clear_profit) == 0:
            self.capital_pd[a_symbol + call_clear_profit] = np.NAN * \
                                                              self.capital_pd.shape[0]

        # 买跌累计平仓盈亏
        put_clear_profit = '_put_clear_profit'
        if columns_list.count(a_symbol + put_clear_profit) == 0:
            self.capital_pd[a_symbol + put_clear_profit] = np.NAN * \
                                                             self.capital_pd.shape[0]

        setattr(self, a_symbol + call_keep, 0)
        setattr(self, a_symbol + put_keep, 0)

        setattr(self, a_symbol + call_worth, 0)
        setattr(self, a_symbol + put_worth, 0)

        setattr(self, a_symbol + call_deposit, 0)
        setattr(self, a_symbol + put_deposit, 0)

        setattr(self, a_symbol + call_holding_price, 0)
        setattr(self, a_symbol + put_holding_price, 0)

        setattr(self, a_symbol + call_holding_profit, 0)
        setattr(self, a_symbol + put_holding_profit, 0)

        setattr(self, a_symbol + call_clear_profit, 0)
        setattr(self, a_symbol + put_clear_profit, 0)

    def apply_init_kl(self, action_pd, show_progress):
        """
        根据回测交易在时序资金对象capital_pd上新建对应的call，put列
        :param action_pd: 回测交易行为对象，pd.DataFrame对象
        :param show_progress: 外部设置是否需要显示进度条
        """
        # 使用set筛选唯一的symbol交易序列
        symbols = set(action_pd.symbol)
        # 单进程进度条
        with AbuProgress(len(symbols), 0, label='apply_init_kl...') as progress:
            for pos, symbol in enumerate(symbols):
                if show_progress:
                    progress.show(a_progress=pos + 1)
                # 迭代symbols，新建对应的call，put列
                self.init_k_line(symbol)

    def apply_k_line(self, a_k_day, kl_pd, buy_type_head):
        """
        在apply_kl中的do_apply_kl方法中时序资金对象capital进行apply的对应方法，
        即迭代金融时间序列的每一个交易日，根据持仓量计算每一个交易日的市场价值
        :param a_k_day: 每一个被迭代中的时间，即每一个交易日数据
        :param kl_pd: 正在被apply迭代的金融时间序列本体，pd.DataFrame对象
        :param buy_type_head: 代表交易类型，范围（_call，_put）
        :return:
        """
        if a_k_day[kl_pd.name + buy_type_head + '_keep'] > 0:
            kl = kl_pd[kl_pd['date'] == a_k_day['date']]
            if kl is None or kl.shape[0] == 0:
                # 前提是当前交易日有对应的持仓
                return

            # 今天的收盘价格
            td_close = kl['close'].values[0]

            if buy_type_head == '_put':
                direction = -1
            else:
                direction = 1

            # 根据持仓量即处理后的今日收盘价格，进行今日价值计算
            self.capital_pd.at[kl.index, kl_pd.name + buy_type_head + '_worth'] \
                = np.round(td_close * a_k_day[kl_pd.name + buy_type_head + '_keep'], 3)

            self.capital_pd.at[kl.index, kl_pd.name + buy_type_head + '_holding_profit'] \
                = np.round((td_close - a_k_day[kl_pd.name + buy_type_head + '_holding_price']) * direction *
                           a_k_day[kl_pd.name + buy_type_head + '_keep'], 3)

    def apply_kl(self, action_pd, kl_pd_manager, show_progress):
        """
        apply_action之后对实际成交的交易分别迭代更新时序资金对象capital_pd上每一个交易日的实时价值
        :param action_pd: 回测结果生成的交易行为构成的pd.DataFrame对象
        :param kl_pd_manager: 金融时间序列管理对象，AbuKLManager实例
        :param show_progress: 是否显示进度条
        """

        # 在apply_action之后形成deal列后，set出考虑资金下成交了的交易序列
        deal_symbols_set = set(action_pd[action_pd['deal'] == 1].symbol)

        def do_apply_kl(kl_pd, buy_type_head):
            """
            根据金融时间序列在时序资金对象capital_pd上进行call（买涨），put（买跌）的交易日实时价值更新
            :param kl_pd: 金融时间序列，pd.DataFrame对象
            :param buy_type_head: 代表交易类型，范围（_call，_put）
            """
            # cash_blance对na进行pad处理
            self.capital_pd['cash_blance'].fillna(method='pad', inplace=True)
            # symbol对应列持仓量对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_keep'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_keep'].fillna(0, inplace=True)

            # symbol对应列持仓均价对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_holding_price'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_holding_price'].fillna(0, inplace=True)

            # 使用apply在axis＝1上，即每一个交易日上对持仓量及市场价值进行更新
            self.capital_pd.apply(self.apply_k_line, axis=1, args=(kl_pd, buy_type_head))

            # symbol对应列市场价值对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_worth'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_worth'].fillna(0, inplace=True)

            # symbol对应列保证金对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_deposit'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_deposit'].fillna(0, inplace=True)

            # symbol对应列浮动盈亏对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_holding_profit'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_holding_profit'].fillna(0, inplace=True)

            # symbol对应列累计平仓盈亏对na进行处理
            self.capital_pd[kl_pd.name + buy_type_head + '_clear_profit'].fillna(method='pad', inplace=True)
            self.capital_pd[kl_pd.name + buy_type_head + '_clear_profit'].fillna(0, inplace=True)

            # 纠错处理把keep=0但是worth被pad的进行二次修正
            fe_mask = (self.capital_pd[kl_pd.name + buy_type_head + '_keep'] == 0) & (
                self.capital_pd[kl_pd.name + buy_type_head + '_worth'] > 0)
            # 筛出需要纠错的index
            fe_index = self.capital_pd[fe_mask].index
            # 将需要纠错的对应index上市场价值进行归零处理
            cp_w = self.capital_pd[kl_pd.name + buy_type_head + '_worth']
            cp_w.loc[fe_index] = 0

            cp_d = self.capital_pd[kl_pd.name + buy_type_head + '_deposit']
            cp_d.loc[fe_index] = 0

            cp_p = self.capital_pd[kl_pd.name + buy_type_head + '_holding_profit']
            cp_p.loc[fe_index] = 0

        # 单进程进度条
        with AbuProgress(len(deal_symbols_set), 0, label='apply_kl...') as progress:
            for pos, deal_symbol in enumerate(deal_symbols_set):
                if show_progress:
                    progress.show(a_progress=pos + 1)
                # 从kl_pd_manager中获取对应的金融时间序列kl，每一个kl分别进行call（买涨），put（买跌）的交易日实时价值更新
                kl = kl_pd_manager.get_pick_time_kl_pd(deal_symbol)
                kl = day_kline(deal_symbol, kl)

                # 进行call（买涨）的交易日实时价值更新
                do_apply_kl(kl, '_call')
                # 进行put（买跌）的交易日实时价值更新
                do_apply_kl(kl, '_put')

    def apply_action(self, a_action, progress):
        """
        在回测结果生成的交易行为构成的pd.DataFrame对象上进行apply对应本方法，即
        将交易行为根据资金情况进行处理，处理手续费以及时序资金对象capital_pd上的
        数据更新
        :param a_action: 每一个被迭代中的action，即每一个交易行为
        :param progress: 进度条对象
        :return: 是否成交deal bool
        """
        # 区别买入行为和卖出行为
        is_buy = True if a_action['action'] == 'buy' else False
        # 从action数据构造AbuOrder对象
        order = AbuOrder()
        order.buy_symbol = a_action['symbol']
        order.buy_cnt = a_action['Cnt']
        if is_buy:
            # 如果是买单，sell_price = price2 ,详情阅读ABuTradeExecute中transform_action
            order.buy_price = a_action['Price']
            order.sell_price = a_action['Price2']
        else:
            # 如果是卖单，buy_price = price2 ,详情阅读ABuTradeExecute中transform_action
            order.sell_price = a_action['Price']
            order.buy_price = a_action['Price2']
        # 交易发生的时间
        order.buy_date = a_action['Date']
        order.sell_date = a_action['Date']

        order.buy_datetime = a_action['Datetime']
        order.sell_datetime = a_action['Datetime']
        # 交易的方向
        order.expect_direction = a_action['Direction']

        # 对买单和卖单分别进行处理，确定是否成交deal
        deal = self.buy_stock(order) if is_buy else self.sell_stock(order)

        if progress is not None:
            progress.show()

        return deal

    def buy_stock(self, a_order):
        """
        在apply_action中每笔交易进行处理，根据买单计算cost，在时序资金对象capital_pd上修改对应cash_blance，
        以及更新对应symbol上的持仓量
        :param a_order: 在apply_action中由action转换的AbuOrder对象
        :return: 是否成交deal bool
        """

        # 首先使用commission对象计算手续费
        # with self.commission.buy_commission_func(a_order) as (buy_func, commission_list):
        #     commission = buy_func(a_order.buy_cnt, a_order.buy_price)
        #     # 将上下文管理器中返回的commission_list中添加计算结果commission，内部根据list长度决定写入手续费记录pd.DataFrame
        #     commission_list.append(commission)

        # cost = 买单数量 ＊ 单位价格 ＋ 手续费
        # order_cost = a_order.buy_cnt * a_order.buy_price + commission

        commission = query_commission(a_order.buy_cnt, a_order.buy_price, a_order.buy_symbol)

        deposit = query_deposit(a_order.buy_cnt, a_order.buy_price, a_order.buy_symbol)
        order_cost = deposit + commission

        # 买单时间转换成pd时间日期对象
        time_ind = pd.to_datetime(ABuDateUtil.fmt_date(a_order.buy_date))

        # 判定买入时刻的cash值是否能够钱买入
        if self.cash_balance >= order_cost and a_order.buy_cnt > 0:
            self.sum_commission += commission
            # 够的话，买入，先将cash － cost
            self.cash_balance -= order_cost

            # 根据a_order.expect_direction确定是要更新call的持仓量还是put的持仓量
            buy_type_keep = '_call_keep' if a_order.expect_direction == 1.0 else '_put_keep'
            buy_type_deposit = '_call_deposit' if a_order.expect_direction == 1.0 else '_put_deposit'
            buy_type_holding_price = '_call_holding_price' if a_order.expect_direction == 1.0 else '_put_holding_price'
            buy_type_clear_profit = '_call_clear_profit' if a_order.expect_direction == 1.0 else '_put_clear_profit'

            keep_cnt = getattr(self, a_order.buy_symbol + buy_type_keep)
            deposit_cnt = getattr(self, a_order.buy_symbol + buy_type_deposit)
            holding_average_price = getattr(self, a_order.buy_symbol + buy_type_holding_price)
            clear_profit = getattr(self, a_order.buy_symbol + buy_type_clear_profit)
            clear_profit -= commission

            holding_average_price = (holding_average_price * keep_cnt + a_order.buy_price * a_order.buy_cnt) / \
                                    (keep_cnt + a_order.buy_cnt)
            keep_cnt += a_order.buy_cnt
            deposit_cnt += deposit

            self.capital_pd.at[time_ind, 'cash_blance'] = np.round(self.cash_balance, 3)

            # 在更新持仓量前，取出之前的数值
            # org_cnt = self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_keep]
            # 更新持仓量
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_keep] = keep_cnt
            # 更新保证金
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_deposit] = deposit_cnt
            # 更新持仓均价
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_holding_price] = holding_average_price
            # 更新累计平仓盈亏
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_clear_profit] = clear_profit

            setattr(self, a_order.buy_symbol + buy_type_keep, keep_cnt)
            setattr(self, a_order.buy_symbol + buy_type_deposit, deposit_cnt)
            setattr(self, a_order.buy_symbol + buy_type_holding_price, holding_average_price)
            setattr(self, a_order.buy_symbol + buy_type_clear_profit, clear_profit)

            return True
        else:
            return False

    def sell_stock(self, a_order):
        """
        在apply_action中每笔交易进行处理，根据卖单计算cost，在时序资金对象capital_pd上修改对应cash_blance，
        以及更新对应symbol上的持仓量
        :param a_order: 在apply_action中由action转换的AbuOrder对象
        :return: 是否成交deal bool
        """

        # 卖单时间转换成pd时间日期对象
        time_ind = pd.to_datetime(ABuDateUtil.fmt_date(a_order.sell_date))

        # 根据a_order.expect_direction确定是要更新call的持仓量还是put的持仓量
        buy_type_keep = '_call_keep' if a_order.expect_direction == 1.0 else '_put_keep'
        buy_type_deposit = '_call_deposit' if a_order.expect_direction == 1.0 else '_put_deposit'
        buy_type_holding_price = '_call_holding_price' if a_order.expect_direction == 1.0 else '_put_holding_price'
        buy_type_clear_profit = '_call_clear_profit' if a_order.expect_direction == 1.0 else '_put_clear_profit'

        keep_cnt = getattr(self, a_order.buy_symbol + buy_type_keep)
        deposit_cnt = getattr(self, a_order.buy_symbol + buy_type_deposit)
        holding_average_price = getattr(self, a_order.buy_symbol + buy_type_holding_price)
        clear_profit = getattr(self, a_order.buy_symbol + buy_type_clear_profit)

        sell_cnt = a_order.buy_cnt if keep_cnt > a_order.buy_cnt else keep_cnt

        if keep_cnt > 0:
            keep_cnt -= sell_cnt

            holding_average_price = 0 if keep_cnt == 0 else (holding_average_price * (keep_cnt + sell_cnt) - sell_cnt *
                                                             a_order.buy_price) / keep_cnt

            sell_earn_price = (a_order.sell_price - a_order.buy_price) * a_order.expect_direction

            deposit = query_deposit(sell_cnt, a_order.buy_price, a_order.buy_symbol)
            order_earn = sell_earn_price * sell_cnt + deposit

            # 更新保证金
            deposit_cnt -= deposit
            commission = query_commission(sell_cnt, a_order.sell_price, a_order.buy_symbol)
            clear_profit += sell_earn_price * sell_cnt - commission

            self.sum_commission += commission

            self.cash_balance += (order_earn - commission)

            self.capital_pd.at[time_ind, 'cash_blance'] = np.round(self.cash_balance, 3)

            # 更新持仓量
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_keep] = keep_cnt
            # 更新保证金
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_deposit] = deposit_cnt
            # 更新持仓均价
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_holding_price] = holding_average_price
            # 更新累计平仓均价
            self.capital_pd.at[time_ind, a_order.buy_symbol + buy_type_clear_profit] = clear_profit

            setattr(self, a_order.buy_symbol + buy_type_keep, keep_cnt)
            setattr(self, a_order.buy_symbol + buy_type_deposit, deposit_cnt)
            setattr(self, a_order.buy_symbol + buy_type_holding_price, holding_average_price)
            setattr(self, a_order.buy_symbol + buy_type_clear_profit, clear_profit)

            return True

        else:
            return False
