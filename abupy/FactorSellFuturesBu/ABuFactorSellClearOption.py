# -*- encoding:utf-8 -*-
"""
    突破期权建仓时设定价格平仓因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import numpy as np

from .ABuFactorSellFuturesBase import AbuFactorSellFuturesBase, ESupportDirection


class AbuFactorSellClearCall(AbuFactorSellFuturesBase):

    __slots__ = ('sell_type_extra', 'today_ind')

    def _init_self(self, **kwargs):
        pass
        # 在输出生成的orders_pd中显示的名字
        # self.sell_type_extra = '{}'.format(self.__class__.__name__)

    def read_fit_day(self, today, undone_orders, holding_object, buy_factor):

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.values[14])
        done_orders = list()

        if buy_factor.holding_cnt == 0:
            return done_orders, undone_orders, None

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        # orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, undone_orders, holding_object, buy_factor)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def remove_clear_option(self, option_list, clear_option_list):

        new_list = list(set(option_list) - set(clear_option_list))

        new_list.sort(key=option_list.index)

        return new_list

    def fit_day(self, today, orders, holding_object, buy_factor):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_object: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :param buy_factor: 实例化的买入因子
        """
        self.sell_type_extra = '{}:dynamic_{}_{}_{}'.format(self.__class__.__name__, buy_factor.is_dynamic,
                                                            buy_factor.option_clear_proportion, buy_factor.xd_option)
        option_cleared_list = list()
        sell_cnt = 0
        for option in buy_factor.option_list:

            if today.close < option.clear_price:

                option.profit = (np.maximum((today.close - option.k) * option.cp, 0) - option.initial_value) * \
                                option.num * option.direction
                option.win = 1 if option.profit > 0 else 0
                option.matured_price = today.close
                option.maturity_date = today.date
                option.clear_datetime = today.datetime

                sell_cnt += abs(option.delta)
                option_cleared_list.append(option)

        if sell_cnt:

            buy_factor.option_list = self.remove_clear_option(buy_factor.option_list, option_cleared_list)

            self.sell_cnt = sell_cnt

            done_orders, undone_orders = self.sell_tomorrow(orders, holding_object, buy_factor)

            return done_orders, undone_orders, option_cleared_list

        else:
            return [], orders, None


class AbuFactorSellClearPut(AbuFactorSellFuturesBase):

    __slots__ = ('sell_type_extra', 'today_ind')

    def _init_self(self, **kwargs):
        pass
        # 在输出生成的orders_pd中显示的名字
        # self.sell_type_extra = '{}'.format(self.__class__.__name__)

    def read_fit_day(self, today, undone_orders, holding_object, buy_factor):

        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.values[14])
        done_orders = list()

        if buy_factor.holding_cnt == 0:
            return done_orders, undone_orders, None

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        # orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, undone_orders, holding_object, buy_factor)

    def support_direction(self):
        """支持的方向，只支持正向"""
        return [ESupportDirection.DIRECTION_CAll.value]

    def remove_clear_option(self, option_list, clear_option_list):

        new_list = list(set(option_list) - set(clear_option_list))

        new_list.sort(key=option_list.index)

        return new_list

    def fit_day(self, today, orders, holding_object, buy_factor):
        """
        寻找向下突破作为策略卖出驱动event
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_object: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :param buy_factor: 实例化的买入因子
        """
        self.sell_type_extra = '{}:dynamic_{}_{}_{}'.format(self.__class__.__name__, buy_factor.is_dynamic,
                                                            buy_factor.option_clear_proportion, buy_factor.xd_option)
        option_cleared_list = list()
        sell_cnt = 0
        for option in buy_factor.option_list:

            if today.close > option.clear_price:
                option.profit = (np.maximum((today.close - option.k) * option.cp, 0) - option.initial_value) * \
                                option.num * option.direction
                option.win = 1 if option.profit > 0 else 0
                option.matured_price = today.close
                option.maturity_date = today.date
                option.clear_datetime = today.datetime

                sell_cnt += abs(option.delta)
                option_cleared_list.append(option)

        if sell_cnt:

            buy_factor.option_list = self.remove_clear_option(buy_factor.option_list, option_cleared_list)

            self.sell_cnt = sell_cnt

            done_orders, undone_orders = self.sell_tomorrow(orders, holding_object, buy_factor)

            return done_orders, undone_orders, option_cleared_list

        else:
            return [], orders, None
