# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from abc import ABCMeta, abstractmethod
import six
import QuantLib as Ql

from . import OptionHedge


calendar = Ql.China()


class OptionHedgeBase(six.with_metaclass(ABCMeta, object)):

    @abstractmethod
    def calc_delta(self, *args, **kwargs):
        pass

    @abstractmethod
    def calc_price(self, *args, **kwargs):
        pass

    def get_quantlib_date(self, date):

        year, month, day = OptionHedge.split_date_int(date)

        return Ql.Date(day, month, year)

    # noinspection PyMethodMayBeStatic
    def get_maturity_date(self, start_date, n):
        """
        用于期权对冲模块，根据起始日期和后推天数得到后推的日期
        :param start_date: 起始日期，int格式
        :param n: int格式
        :return: 到期日期，int格式，多进程情况下不能pickle SwigPyObject对象，故只存为int
        """

        date = self.get_quantlib_date(start_date)
        maturity_date = calendar.advance(date, Ql.Period(n, Ql.Days))

        result = OptionHedge.to_date_int(maturity_date.year(), maturity_date.month(), maturity_date.dayOfMonth())

        return result

    # noinspection PyMethodMayBeStatic
    def get_num_between_dates(self, calculation_date, maturity_date):
        """
        用于期权对冲模块，根据起始日期和到期日期得到间隔天数
        :param calculation_date: 起始日期，QuantLib Date格式
        :param maturity_date: QuantLib Date格式
        :return: int格式
        """

        t = calendar.businessDaysBetween(calculation_date, maturity_date) + 1
        return t
