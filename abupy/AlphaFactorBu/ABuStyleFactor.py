# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..UtilBu import ABuRegUtil


class AbuStyleFactor(object):

    def beta(self, symbol, end=None):

        symbol_ret_series = self.ret[-250:].ewm(halflife=60).mean()
        benchmark_ret_series = self.benchmark.ret[-250:].ewm(halflife=60).mean()

        result = ABuRegUtil.regress_xy(symbol_ret_series, benchmark_ret_series)[2][0]

        return result
