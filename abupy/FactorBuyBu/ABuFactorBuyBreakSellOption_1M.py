# -*- encoding:utf-8 -*-
"""
    买入择时示例因子：突破卖出期权择时因子
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from .ABuFactorBuyBase import AbuFactorBuyBase, BuyCallMixin, BuyPutMixin
from ..UtilBu.ABuKlineUtil import min_kline
from ..UtilBu import ABuEuroOptionUtil
from ..UtilBu.ABuStrUtil import get_letters, get_num_from_str
from ..CoreBu.ABuEnv import g_trade_date_list, g_futures_kline_num_dict


s_threshold = 0.05


# noinspection PyAttributeOutsideInit
class AbuFactorBuyBreakSellOption1M(AbuFactorBuyBase, BuyCallMixin):
    """示例正向突破买入择时类，混入BuyCallMixin，即向上突破触发卖出看跌期权event"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        self.cp = kwargs['cp']
        self.direction = kwargs['direction']
        self.maturity = kwargs['maturity']
        self.nominal_money = kwargs['nominal_money']
        self.date_type = kwargs['date_type']
        self.rate = kwargs['rate']
        self.dividend = kwargs['dividend']

        self.sell_factors = kwargs['sell_factors']
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:{}'.format(self.__class__.__name__, self.xd)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = get_num_from_str(kwargs['freq'])
        self.kline_num = g_futures_kline_num_dict[kwargs['freq']][get_letters(self.kl_pd.name)]
        # 输出根据特定频率下合成的行情数据
        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

        # 信号产生列表，多次突破可能产生多个信号
        self.signal_list = list()

        # 载入特定合约的波动率表
        self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.kl_pd.name))
        # 记录产生信号的日期，用于排除同一天内产生多个信号
        self.check_signal = self.kl_pd.date[0]

    def form_signal(self, today):

        # if self.today_ind < self.xd * self.kline_num - 1:
        #     return False
        #     # 今天的收盘价格达到xd天内最高价格则符合买入条件

        if self.check_signal == today.date:
            return False

        if today.close == self.freq_kl_pd.close[self.today_ind - self.xd * self.kline_num + 1:self.today_ind + 1].max():
            self.check_signal = today.date
            return True

        return False

    def fit_day(self, today, holding_cnt):

        _check_if = self.check_dominant_today(today)

        if not _check_if:
            return None

        signal = self.form_signal(today)
        s = today.close
        yesterday_date = g_trade_date_list[g_trade_date_list.index(today.date) - 1]
        vol = round(self.vol_df.at[yesterday_date, 'Close_to_Close_Vol'], 4)

        if signal:
            idx = g_trade_date_list.index(today.date)
            maturity_date = g_trade_date_list[idx+self.maturity]

            self.signal_list.append({'strike': s, 'rate': self.rate, 'dividend': self.dividend,
                                     'maturity_date': maturity_date, 'cp': self.cp, 'date_type': self.date_type,
                                     'direction': self.direction, 'nominal_num': round(self.nominal_money / s / vol, 2)})

        if self.signal_list:
            print('buy call')
            print(today.date)
            cnt = 0
            for option_info_dict in self.signal_list:
                k = option_info_dict['strike']
                r = option_info_dict['rate']
                q = option_info_dict['dividend']
                t = g_trade_date_list.index(option_info_dict['maturity_date']) - g_trade_date_list.index(today.date)
                cp = option_info_dict['cp']
                date_type = option_info_dict['date_type']
                direction = option_info_dict['direction']
                num = option_info_dict['nominal_num']
                # print('vol :', vol)

                delta = 0 if t < 1 else ABuEuroOptionUtil.bs_delta(s, k, r, q, t, vol, cp, date_type) * direction
                # print('delta')
                # print(delta)

                cnt += num * delta
            # print(self.signal_list)
            print('symbol: ', self.kl_pd.name)
            print('cnt: ', cnt)
            print('********')
            print()
            hc = self.expect_direction * holding_cnt

            if cnt - hc > s_threshold * cnt:
                self.buy_cnt = cnt - hc
                return self.buy_tomorrow(holding_cnt)

            return None

        return None


# noinspection PyAttributeOutsideInit
class AbuFactorBuyPutBreakSellOption1M(AbuFactorBuyBase, BuyPutMixin):
    """示例反向突破买入择时类，混入BuyPutMixin，即向下突破触发买入看涨期权event"""

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 突破参数 xd， 比如20，30，40天...突破, 不要使用kwargs.pop('xd', 20), 明确需要参数xq
        self.xd = kwargs['xd']
        self.cp = kwargs['cp']
        self.direction = kwargs['direction']
        self.maturity = kwargs['maturity']
        self.nominal_money = kwargs['nominal_money']
        self.date_type = kwargs['date_type']
        self.rate = kwargs['rate']
        self.dividend = kwargs['dividend']

        self.sell_factors = kwargs['sell_factors']
        # 在输出生成的orders_pd中显示的名字
        self.factor_name = '{}:{}'.format(self.__class__.__name__, self.xd)

        # 均线频率参数 freq， 比如5，15，30分钟.., 形如 '5M'代表5分钟线
        self.freq = get_num_from_str(kwargs['freq'])
        self.kline_num = g_futures_kline_num_dict[kwargs['freq']][get_letters(self.kl_pd.name)]
        # 输出根据特定频率下合成的行情数据
        self.freq_kl_pd = min_kline(self.kl_pd.name, self.kl_pd, self.freq)

        # 信号产生列表，多次突破可能产生多个信号
        self.signal_list = list()

        # 载入特定合约的波动率表
        self.vol_df = ABuEuroOptionUtil.load_vol_df(get_letters(self.kl_pd.name))
        # 记录产生信号的日期，用于排除同一天内产生多个信号
        self.check_signal = self.kl_pd.date[0]

    def form_signal(self, today):

        # if self.today_ind < self.xd * self.kline_num - 1:
        #     return False
        # 今天的收盘价格达到xd天内最高价格则符合买入条件

        if self.check_signal == today.date:
            return False

        if today.close == self.freq_kl_pd.close[self.today_ind - self.xd * self.kline_num + 1:self.today_ind + 1].min():
            self.check_signal = today.date
            return True

        return False

    def fit_day(self, today, holding_cnt):

        _check_if = self.check_dominant_today(today)

        if not _check_if:
            return None

        signal = self.form_signal(today)
        s = today.close
        yesterday_date = g_trade_date_list[g_trade_date_list.index(today.date) - 1]
        vol = round(self.vol_df.at[yesterday_date, 'Close_to_Close_Vol'], 4)

        if signal:
            print('signal create')
            print(today.date)
            print()
            idx = g_trade_date_list.index(today.date)
            maturity_date = g_trade_date_list[idx+self.maturity]

            self.signal_list.append({'strike': s, 'rate': self.rate, 'dividend': self.dividend,
                                     'maturity_date': maturity_date, 'cp': self.cp, 'date_type': self.date_type,
                                     'direction': self.direction, 'nominal_num': round(self.nominal_money / s / vol, 2)})

        if self.signal_list:
            print('buy put')
            print(today.datetime)
            cnt = 0
            for option_info_dict in self.signal_list:
                k = option_info_dict['strike']
                r = option_info_dict['rate']
                q = option_info_dict['dividend']
                t = g_trade_date_list.index(option_info_dict['maturity_date']) - g_trade_date_list.index(today.date)
                cp = option_info_dict['cp']
                date_type = option_info_dict['date_type']
                direction = option_info_dict['direction']
                num = option_info_dict['nominal_num']
                print('vol :', vol)

                delta = 0 if t < 1 else ABuEuroOptionUtil.bs_delta(s, k, r, q, t, vol, cp, date_type) * direction
                print('delta')
                print(delta)

                cnt += num * delta * self.expect_direction
            print(self.signal_list)
            print('cnt: ', cnt)
            print('********')
            print()

            if cnt - holding_cnt > s_threshold * cnt:
                self.buy_cnt = cnt - holding_cnt
                return self.buy_tomorrow(holding_cnt)

            return None

        return None
