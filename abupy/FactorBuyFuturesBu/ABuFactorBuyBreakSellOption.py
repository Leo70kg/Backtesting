# -*- encoding:utf-8 -*-
"""
    买入择时示例因子：突破卖出期权择时因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import numpy as np

from .ABuFactorBuyFuturesBase import AbuFactorBuyFuturesBase, BuyCallMixin, BuyPutMixin
from ..UtilBu import ABuEuroOptionUtil
from ..UtilBu.ABuStrUtil import get_letters
from ..OptionHedgeBu import AbuEuroOptionHedge


# noinspection PyAttributeOutsideInit
class AbuFactorBuyBreakSellOption(AbuFactorBuyFuturesBase, BuyCallMixin):
    """示例正向突破买入择时类，混入BuyCallMixin，即向上突破触发卖出看跌期权event"""

    __slots__ = ('xd', 'cp', 'direction', 'maturity', 'premium', 'notional', 'calendar_type', 'high_ndarray',
                 'rate', 'dividend', 'hedge_threshold', 'sell_factors', 'factor_name', 'freq', 'low_ndarray',
                 'freq_kl_pd', 'kline_num', 'close_ndarray', 'start_date', 'end_date', 'option_list', 'option_max_num',
                 'vol_df', 'check_signal', 'today_time_str_idx', 'freq_kl_pd_time_str', 'time_ndarray', 'is_dynamic',
                 'option_low_price', 'option_high_price', 'option_clear_proportion')

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        self.xd_option = kwargs['xd1']
        self.cp = kwargs['cp']
        self.direction = kwargs['direction']
        self.maturity = kwargs['maturity']
        self.premium = kwargs['premium']
        self.notional = kwargs['notional']
        self.calendar_type = kwargs['calendar_type']
        self.rate = kwargs['rate']
        self.dividend = kwargs['dividend']

        self.hedge_threshold = kwargs['threshold']
        self.sell_factors = kwargs['sell_factors']
        self.option_max_num = kwargs['option_max_num']
        self.option_clear_proportion = kwargs['option_clear_proportion']
        self.is_dynamic = kwargs['dynamic']

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = kwargs['freq'].upper()
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:{}_{}, max_{}_options'.format(self.__class__.__name__, self.xd, self.freq,
                                                             self.option_max_num)

        self.symbol = self.kl_pd.name

        self.freq_kl_pd, self.kline_num = self.get_freq_kl_pd(self.kl_pd, self.freq, self.kl_pd_dict)

        self.close_ndarray = self.freq_kl_pd.close.values
        self.high_ndarray = self.freq_kl_pd.high.values
        self.low_ndarray = self.freq_kl_pd.low.values
        self.open_ndarray = self.freq_kl_pd.open.values

        self.start_date, self.end_date = self.get_contract_start_and_end_date(self.symbol)

        # 信号产生列表，多次突破可能产生多个信号，记录当前持有的期权头寸
        self.option_list = list()

        # 载入特定合约的波动率表
        self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.symbol))
        # 记录产生信号的日期，用于排除同一天内产生多个信号
        self.check_signal = self.kl_pd.date[0]
        self.option_low_price = None
        self.option_high_price = None

        self.check_vol_date = self.kl_pd.date[0]
        self.vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, self.check_vol_date, 1)

        self.today_time_str_idx = self.get_today_time_str_idx(self.freq)

        self.freq_kl_pd_time_str = self.get_freq_kl_pd_time_str(self.freq)
        self.time_ndarray = self.freq_kl_pd[self.freq_kl_pd_time_str].values

    def form_signal(self, today):

        if today.date > self.end_date or today.date < self.start_date:
            return False

        today_ind = np.where(self.time_ndarray == today.values[self.today_time_str_idx])[0][0]

        if today_ind < np.maximum(self.xd, self.xd_option):
            return False

        # if self.close_ndarray[today_ind-1] - self.open_ndarray[today_ind-1] < 0:
        #     return False

        if self.check_signal == today.date:
            return False

        # 今天的收盘价格达到xd天内最高价格则符合买入条件
        # if today.close == self.close_ndarray[self.today_ind - self.xd * self.kline_num + 1:self.today_ind + 1].max():

        if today.close > self.high_ndarray[today_ind - self.xd: today_ind].max():
            self.check_signal = today.date
            self.option_low_price = self.low_ndarray[today_ind - self.xd_option: today_ind].min()
            self.option_high_price = self.high_ndarray[today_ind - self.xd_option: today_ind].max()

            # self.option_clear_price = (self.low_ndarray[today_ind - self.xd_option: today_ind].min() +
            #                            self.high_ndarray[today_ind - self.xd_option: today_ind].max()) / 2

            return True

        return False

    def fit_day(self, today, holding_object):

        mid_var = None

        # if self.check_dominant_today(today.date, self.start_date, self.end_date):
        #     return None, mid_var
        if today.date != self.check_vol_date:
            self.vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, today.date, 1)
            self.check_vol_date = today.date

        signal = self.form_signal(today)
        s = today.close
        # vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, today.date, 1)

        if signal:

            if len(self.option_list) >= self.option_max_num:
                pass

            else:
                option = AbuEuroOptionHedge(s, self.rate, self.dividend, self.maturity, self.vol, self.cp,
                                            self.calendar_type, self.direction, today.date, today.datetime, self.symbol)

                option.initial_value = option.calc_price(s, self.vol)
                option.low_price = self.option_low_price
                option.high_price = self.option_high_price

                option.clear_price = (option.high_price - option.low_price) * self.option_clear_proportion + \
                    option.low_price

                self.option_list.append(option)

                # option.num_in_list = self.option_list.index(option) + 1
                option.num_in_list = len(self.option_list)

                option.num = round(self.notional / s / self.vol, 2) if self.premium is None else \
                    round(self.premium / option.initial_value, 2)

        if self.option_list:
            # print('buy call')
            # print(today.date)
            cnt = 0
            # print(today.datetime, 'call', s)
            for option in self.option_list:
                option.delta = option.calc_delta(s, self.vol, today.date) * option.num

                if option.delta / option.num > 0.95 and abs(s - option.k) > option.k * self.vol / np.sqrt(252) * 4:
                    option.k = s
                    option.delta = option.calc_delta(s, self.vol, today.date) * option.num * self.expect_direction

                if self.is_dynamic:
                    # option.low_price = np.minimum(option.low_price, today.low)
                    option.high_price = np.maximum(option.high_price, today.high)

                    option.clear_price = (option.high_price - option.low_price) * self.option_clear_proportion + \
                        option.low_price
                # print(option.delta)
                cnt += option.delta

            # print(today.datetime)
            # print(cnt, self.holding_cnt)
            # print()
            threshold_cnt = self.hedge_threshold * cnt

            hc = self.expect_direction * self.holding_cnt

            # print('holding_cnt: ', hc, ' ', 'cnt: ', cnt, ' ', 'threshold_cnt: ', threshold_cnt)
            # print()
            if cnt - hc > threshold_cnt:
                self.buy_cnt = cnt - hc

                order = self.buy_tomorrow(holding_object)

                return order, mid_var

            return None, mid_var

        return None, mid_var


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutBreakSellOption(AbuFactorBuyFuturesBase, BuyPutMixin):
    """示例反向突破买入择时类，混入BuyPutMixin，即向下突破触发买入看涨期权event"""

    __slots__ = ('xd', 'cp', 'direction', 'maturity', 'premium', 'notional', 'calendar_type', 'low_ndarray',
                 'rate', 'dividend', 'hedge_threshold', 'sell_factors', 'factor_name', 'freq', 'option_clear_price',
                 'freq_kl_pd', 'kline_num', 'close_ndarray', 'start_date', 'end_date', 'option_list', 'high_ndarray',
                 'vol_df', 'check_signal', 'today_time_str_idx', 'freq_kl_pd_time_str', 'time_ndarray', 'is_dynamic',
                 'option_max_num', 'option_low_price', 'option_high_price', 'option_clear_proportion')

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        self.xd_option = kwargs['xd1']      # 设置期权平仓价格的周期参数
        self.cp = kwargs['cp']
        self.direction = kwargs['direction']
        self.maturity = kwargs['maturity']
        self.premium = kwargs['premium']
        self.notional = kwargs['notional']
        self.calendar_type = kwargs['calendar_type']
        self.rate = kwargs['rate']
        self.dividend = kwargs['dividend']
        self.hedge_threshold = kwargs['threshold']
        self.sell_factors = kwargs['sell_factors']
        self.option_max_num = kwargs['option_max_num']
        self.option_clear_proportion = kwargs['option_clear_proportion']
        self.is_dynamic = kwargs['dynamic']

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = kwargs['freq'].upper()
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:{}_{}, max_{}_options'.format(self.__class__.__name__, self.xd, self.freq,
                                                             self.option_max_num)
        self.symbol = self.kl_pd.name

        self.freq_kl_pd, self.kline_num = self.get_freq_kl_pd(self.kl_pd, self.freq, self.kl_pd_dict)

        self.close_ndarray = self.freq_kl_pd.close.values
        self.high_ndarray = self.freq_kl_pd.high.values
        self.low_ndarray = self.freq_kl_pd.low.values
        self.open_ndarray = self.freq_kl_pd.open.values

        self.start_date, self.end_date = self.get_contract_start_and_end_date(self.symbol)

        # 信号产生列表，多次突破可能产生多个信号
        self.option_list = list()

        # 载入特定合约的波动率表
        self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.symbol))
        # 记录产生信号的日期，用于排除同一天内产生多个信号
        self.check_signal = self.kl_pd.date[0]
        self.option_low_price = None
        self.option_high_price = None

        self.check_vol_date = self.kl_pd.date[0]
        self.vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, self.check_vol_date, 1)

        self.today_time_str_idx = self.get_today_time_str_idx(self.freq)
        self.freq_kl_pd_time_str = self.get_freq_kl_pd_time_str(self.freq)

        self.time_ndarray = self.freq_kl_pd[self.freq_kl_pd_time_str].values

    def form_signal(self, today):

        # if self.check_dominant_today(today.date, self.start_date, self.end_date):
        #     return False

        if today.date > self.end_date or today.date < self.start_date:
            return False

        today_ind = np.where(self.time_ndarray == today.values[self.today_time_str_idx])[0][0]

        if today_ind < np.maximum(self.xd, self.xd_option):
            return False

        if self.check_signal == today.date:
            return False

        # if self.close_ndarray[today_ind-1] - self.open_ndarray[today_ind-1] > 0:
        #     return False

        if today.close < self.low_ndarray[today_ind - self.xd: today_ind].min():
            self.check_signal = today.date
            self.option_low_price = self.low_ndarray[today_ind - self.xd_option: today_ind].min()
            self.option_high_price = self.high_ndarray[today_ind - self.xd_option: today_ind].max()

            return True

        return False

    def fit_day(self, today, holding_object):

        mid_var = None

        if today.date != self.check_vol_date:
            self.vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, today.date, 1)
            self.check_vol_date = today.date

        signal = self.form_signal(today)
        s = today.close
        # vol = ABuEuroOptionUtil.get_vol_n_days_before(self.vol_df, today.date, 1)

        if signal:

            if len(self.option_list) >= self.option_max_num:
                pass

            else:
                option = AbuEuroOptionHedge(s, self.rate, self.dividend, self.maturity, self.vol, self.cp,
                                            self.calendar_type, self.direction, today.date, today.datetime, self.symbol)

                option.initial_value = option.calc_price(s, self.vol)
                option.low_price = self.option_low_price
                option.high_price = self.option_high_price

                option.clear_price = (option.high_price - option.low_price) * (1 - self.option_clear_proportion) + \
                    option.low_price

                self.option_list.append(option)
                # option.num_in_list = self.option_list.index(option) + 1
                option.num_in_list = len(self.option_list)

                option.num = round(self.notional / s / self.vol, 2) if self.premium is None else \
                    round(self.premium / option.initial_value, 2)

        if self.option_list:
            cnt = 0
            # print(today.datetime, 'put', s)
            for option in self.option_list:
                option.delta = option.calc_delta(s, self.vol, today.date) * option.num * self.expect_direction

                if option.delta / option.num > 0.95 and abs(s - option.k) > option.k * self.vol / np.sqrt(252) * 4:

                    option.k = s
                    option.delta = option.calc_delta(s, self.vol, today.date) * option.num * self.expect_direction

                if self.is_dynamic:
                    option.low_price = np.minimum(option.low_price, today.low)
                    # option.high_price = np.maximum(option.high_price, today.high)

                    option.clear_price = (option.high_price - option.low_price) * (1 - self.option_clear_proportion) + \
                        option.low_price
                # print(option.delta)
                cnt += option.delta

            threshold_cnt = self.hedge_threshold * cnt
            hc = self.holding_cnt

            # print('holding_cnt: ', hc, ' ', 'cnt: ', cnt, ' ', 'threshold_cnt: ', threshold_cnt)
            # print()

            if cnt - hc > threshold_cnt:
                self.buy_cnt = cnt - hc
                order = self.buy_tomorrow(holding_object)

                return order, mid_var

            return None, mid_var

        return None, mid_var
