# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .OptionHedgeBase import OptionHedgeBase
from . import OptionHedge


class AbuEuroOptionHedgeHf(OptionHedgeBase):

    __slots__ = ('k', 'r', 'q', 't', 'cp', 'calendar_type', 'direction', 'today_date', 'clear_price',
                 'maturity_date', 'num_in_list', 'initial_value', 'is_matured', 'profit', 'win')

    def __init__(self, k, r, q, t, vol, cp, calendar_type, direction, today_date, today_datetime, symbol):
        self.k = k
        self.r = r
        self.q = q
        self.maturity_days = t
        self.last_days = t

        self.vol = vol
        self.cp = cp
        self.calendar_type = calendar_type  # 1代表252个交易日，0代表365自然日
        self.direction = direction
        self.symbol = symbol

        self.initial_datetime = today_datetime
        self.today_date = today_date
        self.hour = int(today_datetime[11:13])

        self.maturity_date = self.get_maturity_date(today_date, t)

        self.clear_price = None
        self.num_in_list = 0
        self.initial_value = 0

        self.num = 0
        self.is_matured = 0
        self.win = False
        self.profit = 0     # 到期盈利
        self.matured_price = None
        self.revised_k = None

    def __str__(self):
        """打印对象显示"""
        return 'Symbol = ' + str(self.symbol) + '  ' \
               + 'Strike = ' + str(self.k) + '  ' \
               + 'maturity days = ' + str(self.maturity_days) + '  ' \
               + 'initial datetime = ' + str(self.initial_datetime) + '  ' \
               + 'last days = ' + str(self.last_days) + '  ' \
               + 'vol = ' + str(self.vol) + '  ' \
               + 'cp = ' + str(self.cp) + '  ' \
               + 'direction = ' + str(self.direction) + '  ' \
               + 'num in list = ' + str(self.num_in_list) + '  ' \
               + 'amount = ' + str(self.num) + '  ' \
               + 'initial value = ' + str(self.initial_value) + '  ' \
               + 'matured price = ' + str(self.matured_price) + '  ' \
               + 'win = ' + str(self.win) + '  ' \
               + 'profit = ' + str(self.profit) + '  ' \
               + 'clear_price = ' + str(self.clear_price)

    __repr__ = __str__

    def calc_price(self, s, vol):
        """计算期权价值"""

        t = OptionHedge.convert_hour_to_year(self.maturity_days, self.calendar_type)

        price = OptionHedge.price(s, self.k, self.r, self.q, t, vol, self.cp)

        return price

    def calc_delta(self, s, vol, datetime):

        hour = int(datetime[11:13])
        if hour != self.hour:
            self.hour = hour
            self.last_days -= 1

        t = OptionHedge.convert_hour_to_year(self.last_days, self.calendar_type)

        delta = OptionHedge.delta(s, self.k, self.r, self.q, t, vol, self.cp) * self.direction

        return delta
