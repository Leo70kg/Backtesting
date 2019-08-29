# -*- encoding:utf-8 -*-
"""
    卖出择时策略因子基础模块
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from enum import Enum
from copy import deepcopy
from abc import ABCMeta, abstractmethod

from ..CoreBu.ABuFixes import six
# noinspection PyUnresolvedReferences
from ..CoreBu.ABuFixes import filter
from ..CoreBu.ABuBase import AbuParamBase
from ..DataHandlerBu import AbuDataHandler
from ..SlippageBu.ABuSlippageSellMean import AbuSlippageSellMean
from ..SlippageBu.ABuSlippageSellCallTick import AbuSlippageSellCallTick
from ..BetaBu.ABuAtrPosition import AbuAtrPosition
from ..TradeBu.ABuMLFeature import AbuMlFeature
from ..UmpBu.ABuUmpManager import AbuUmpManager
from ..UtilBu.ABuDateUtil import get_minute_from_numpy_datetime64 as get_min
from ..UtilBu.ABuDateUtil import get_hour_from_numpy_datetime64 as get_hour
from ..UtilBu.ABuStrUtil import get_letters

__author__ = '阿布'
__weixin__ = 'abu_quant'


class ESupportDirection(Enum):
    """子策略在support_direction中支持的方向数值定义"""
    DIRECTION_CAll = 1.0
    DIRECTION_PUT = -1.0


class AbuFactorSellFuturesBase(six.with_metaclass(ABCMeta, AbuParamBase)):
    """
        卖出择时策略因子基类：卖出择时策略基类和买入择时基类不同，买入择时
        必须混入一个方向类，代表买涨还是买跌，且只能有一个方向，，卖出策略
        可以同时支持买涨，也可以只支持一个方向
    """

    def __init__(self, capital, kl_pd, kl_pd_dict, benchmark, **kwargs):
        """
        :param capital: 资金类AbuCapital实例化对象
        :param kl_pd: 择时时段金融时间序列，pd.DataFrame对象
        :param kl_pd_dict:用于存储不同的频率下行情数据，dict对象
        :param benchmark: 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        """

        # 择时金融时间序列走势数据
        self.kl_pd = kl_pd
        # 机器学习特征数据构建需要，详情见make_sell_order_ml_feature中构造特征使用
        self.kl_pd_dict = kl_pd_dict
        # 资金情况数据
        self.capital = capital
        # 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        self.benchmark = benchmark

        # 滑点类，默认AbuSlippageSellMean
        self.slippage_class = kwargs.pop('slippage', AbuSlippageSellCallTick)

        # 仓位管理，默认AbuAtrPosition
        self.position_class = kwargs.pop('position', AbuAtrPosition)

        self.position_kwargs = dict()

        # 构造ump对外的接口对象UmpManager
        self.ump_manger = AbuUmpManager(self)

        # 默认的卖出说明，子类通过_init_self可覆盖更具体的名字
        self.sell_type_extra = '{}'.format(self.__class__.__name__)

        # 子类继续完成自有的构造
        self._init_self(**kwargs)

    def __str__(self):
        """打印对象显示：class name, slippage, kl_pd.info"""
        return '{}: slippage:{}, \nkl:\n{}'.format(self.__class__.__name__, self.slippage_class, self.kl_pd.info())

    __repr__ = __str__

    def read_fit_day(self, today, undone_orders, holding_object, buy_factor_object):
        """
        在择时worker对象中做日交易的函数，亦可以理解为盘前的一些决策事件处理，
        内部会调用子类实现的fit_day函数
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_object: 卖出交易发生时的持仓量
        :param undone_orders: 买入择时策略中生成的未完成订单序列
        :param buy_factor_object: 是否对应特定的买入因子
        :return: 生成的交易订单AbuOrder对象
        """
        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.values[14])
        # 回测中默认忽略最后一个交易日
        # if self.today_ind >= self.kl_pd.shape[0] - 1:
        #     done_orders = list()
        #     # 中间变量
        #     mid_var = None
        #
        #     return done_orders, undone_orders, mid_var

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        # orders = list(filter(lambda order: order.expect_direction in self.support_direction(), undone_orders))
        return self.fit_day(today, undone_orders, holding_object, buy_factor_object)

    def sell_tomorrow(self, orders, holding_object, buy_factor_object):

        done_orders = list()
        undone_orders = deepcopy(orders)

        selling_cnt = 0
        # sum_sell_cnt = 0

        for order in undone_orders:

            order.fit_sell_order(self.today_ind, holding_object, selling_cnt, self, buy_factor_object)

            if order is None:
                continue

            if order.sell_cnt == 0:
                order.sell_cnt = None
                break

            if order.sell_cnt is None:
                break

            unsold_cnt = order.buy_cnt - order.sell_cnt

            if unsold_cnt == 0:
                "单笔卖出数量等于买入数量"
                done_orders.append(order)
                undone_orders = undone_orders[1:]
                # sum_sell_cnt += order.sell_cnt

                break

            elif unsold_cnt < 0:
                "单笔卖出数量大于买入数量"
                order.sell_cnt = order.buy_cnt
                done_orders.append(order)
                undone_orders = undone_orders[1:]
                # sum_sell_cnt += order.buy_cnt

                selling_cnt = -unsold_cnt

            else:
                "单笔卖出数量小于买入数量"

                order.buy_cnt = order.sell_cnt
                done_orders.append(order)

                new_order = deepcopy(order)

                new_order.buy_cnt = unsold_cnt
                new_order.sell_date = None
                new_order.sell_datetime = None
                # 订单卖出类型，keep：持有
                new_order.sell_type = 'keep'
                # 交易日持有天数
                new_order.keep_days = 0

                # 订单卖出价格
                new_order.sell_price = None
                # 订单卖出数量
                new_order.sell_cnt = None
                # 订单卖出额外信息
                new_order.sell_type_extra = ''

                undone_orders[0] = new_order
                # sum_sell_cnt += order.sell_cnt

                break

        return done_orders, undone_orders

    def sell_today(self, order, holding_cnt):
        """
        今天即进行卖出操作，需要不能使用今天的收盘数据等做为fit_day中信号判断，
        适合如比特币非明确一天交易日时间或者特殊情况的卖出信号
        :param order交易订单AbuOrder对象
        :param holding_cnt: 卖出交易发生时的持仓量
        """
        return self.revise_sell_order(order.fit_sell_order(self.today_ind - 1, holding_cnt, self))

    # noinspection PyMethodMayBeStatic
    def get_freq_kl_pd(self, kl_pd, freq, kl_pd_dict):
        """
        根据一分钟k线行情获取特定频率周期下的k线行情，并输出该周期线每日k线数量
        :param kl_pd: 原始一分钟k线行情
        :param freq: 周期频率
        :param kl_pd_dict: 之前已保存在字典中的行情数据，目的为提高效率
        :return:
        """
        freq_kl_pd, kline_num = kl_pd_dict.pop(freq, (None, None))

        if freq_kl_pd is None:
            freq_kl_pd, kline_num = AbuDataHandler.handle_kline(kl_pd, freq, kl_pd.name)
            kl_pd_dict[freq] = (freq_kl_pd, kline_num)

        return freq_kl_pd, kline_num

    # noinspection PyMethodMayBeStatic
    def get_freq_kl_pd_time_str(self, freq):
        """基础数据为每分钟k线，进行每分钟迭代时，在不同频率周期下，得到需要用到的字段名称，‘date’或者‘resampled_datetime’ """

        time_str = 'date' if get_letters(freq) == 'D' else 'datetime'

        return time_str

    # noinspection PyMethodMayBeStatic
    def get_today_time_str(self, freq):
        """基础数据为每分钟k线，进行每分钟迭代时，在不同频率周期下，得到需要用到的字段名称，‘date’或者‘datetime’ """

        time_str = 'date' if get_letters(freq) == 'D' else freq + '_resampled_datetime'

        return time_str

    # noinspection PyMethodMayBeStatic
    def check_freq_today(self, today, freq):
        """
        针对日内跨周期回测，判断当前时间点是否在新的频率周期内
        :param today: 当前驱动的交易日金融时间序列数据
        :param freq: 频率周期
        :return:
        """
        return False if get_min(today.name) % freq != 0 else True

    # noinspection PyMethodMayBeStatic
    def check_daily_today(self, today):

        return True if get_hour(today.name) == 15 else False

    @abstractmethod
    def _init_self(self, **kwargs):
        """子类因子针对可扩展参数的初始化"""
        pass

    @abstractmethod
    def fit_day(self, today, orders, holding_object, buy_factor_object):
        """子类主要需要实现的函数，完成策略因子针对每一个交易日的卖出交易策略"""
        pass

    @abstractmethod
    def support_direction(self):
        """子类需要显视注明自己支持的交易方向"""
        pass

    def make_sell_order(self, order, day_ind):
        """
        根据交易发生的时间索引，依次进行：卖出交易时间序列特征生成，
        决策卖出交易是否拦截，生成特征学习数据，最终返回是否order成交，即订单生效
        :param order: 买入择时策略中生成的订单
        :param day_ind: 卖出交易发生的时间索引，即对应self.kl_pd.key
        :return:
        """

        # 卖出交易时间序列特征生成
        ml_feature_dict = self.make_sell_order_ml_feature(day_ind)
        # 决策卖出交易是否拦截
        block = self.make_ump_block_decision(ml_feature_dict)
        if block:
            return False

        # 如果卖出交易不被拦截，生成特征学习数据
        if order.ml_features is None:
            order.ml_features = ml_feature_dict
        else:
            order.ml_features.update(ml_feature_dict)
        return True

    # noinspection PyUnusedLocal
    def make_ump_block_decision(self, ml_feature_dict):
        """
        输入需要决策的当前卖出交易特征通过ump模块的对外manager对交易进行决策，
        判断是否拦截卖出交易，还是放行卖出交易。子类可复写此方法，即子类策略因子实现
        自己的任意ump组合拦截方式，根据策略的拦截比例需要等等参数确定ump具体策略，
        且对于多种策略并行执行策略本身定制适合自己的拦截策略，提高灵活度
        :param ml_feature_dict: 需要决策的当前卖出时刻交易特征dict
        :return:
        """
        return self.ump_manger.ump_block(ml_feature_dict)

    def make_sell_order_ml_feature(self, day_ind):
        """
         根据卖出交易发生的时间索引构通过AbuMlFeature构建卖出时刻的各个交易特征
         :param day_ind: 交易发生的时间索引，对应self.kl_pd.key
         :return:
         """
        return AbuMlFeature().make_feature_dict(self.kl_pd, self.combine_kl_pd, day_ind, buy_feature=False)

    """TODO: 使用check support方式查询是否支持fit_week，fit_month，上层不再使用hasattr去判断"""
    # def fit_week(self, *args, **kwargs):
    #     pass

    # def fit_month(self, *args, **kwargs):
    #     pass

