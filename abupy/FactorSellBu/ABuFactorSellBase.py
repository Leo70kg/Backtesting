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
from ..SlippageBu.ABuSlippageSellMean import AbuSlippageSellMean
from ..BetaBu.ABuAtrPosition import AbuAtrPosition
from ..TradeBu.ABuMLFeature import AbuMlFeature
from ..UmpBu.ABuUmpManager import AbuUmpManager
from ..UtilBu.ABuDateUtil import get_minute_from_numpy_datetime64 as get_min
from ..UtilBu.ABuDateUtil import get_hour_from_numpy_datetime64 as get_hour

__author__ = '阿布'
__weixin__ = 'abu_quant'


class ESupportDirection(Enum):
    """子策略在support_direction中支持的方向数值定义"""
    DIRECTION_CAll = 1.0
    DIRECTION_PUT = -1.0


class AbuFactorSellBase(six.with_metaclass(ABCMeta, AbuParamBase)):
    """
        卖出择时策略因子基类：卖出择时策略基类和买入择时基类不同，买入择时
        必须混入一个方向类，代表买涨还是买跌，且只能有一个方向，，卖出策略
        可以同时支持买涨，也可以只支持一个方向
    """

    def __init__(self, capital, kl_pd, combine_kl_pd, benchmark, **kwargs):
        """
        :param capital: 资金类AbuCapital实例化对象
        :param kl_pd: 择时时段金融时间序列，pd.DataFrame对象
        :param combine_kl_pd:合并了之前一年时间序列的金融时间序列，pd.DataFrame对象
        :param benchmark: 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        """

        # 择时金融时间序列走势数据
        self.kl_pd = kl_pd
        # 机器学习特征数据构建需要，详情见make_sell_order_ml_feature中构造特征使用
        self.combine_kl_pd = combine_kl_pd
        # 资金情况数据
        self.capital = capital
        # 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        self.benchmark = benchmark

        # 滑点类，默认AbuSlippageSellMean
        self.slippage_class = kwargs.pop('slippage', AbuSlippageSellMean)

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

    def read_fit_day(self, today, holding_cnt, orders):
        """
        在择时worker对象中做日交易的函数，亦可以理解为盘前的一些决策事件处理，
        内部会调用子类实现的fit_day函数
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_cnt: 卖出交易发生时的持仓量
        :param orders: 买入择时策略中生成的订单序列
        :return: 生成的交易订单AbuOrder对象
        """
        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.key)
        # 回测中默认忽略最后一个交易日
        if self.today_ind >= self.kl_pd.shape[0] - 1:
            return orders, 0

        """
            择时卖出因子策略可支持正向，反向，或者两个方向都支持，
            针对order中买入的方向，filter策略,
            根据order支持的方向是否在当前策略支持范围来筛选order
        """
        orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))
        return self.fit_day(today, holding_cnt, orders)

    def sell_tomorrow_orders(self, condition, orders, holding_cnt):

        sell_cnt_list = []

        # 满足触发条件
        if condition:
            selling_cnt = 0

            # for order in orders:
            for i in range(len(orders)):
                order = orders[i]

                revised_order = self.sell_tomorrow(order, holding_cnt, selling_cnt)

                if revised_order is None:
                    # print(1)
                    pass

                elif isinstance(revised_order, str):
                    """需要卖出数量恰好等于一笔买单的数量"""
                    sell_cnt_list.append(order.sell_cnt)
                    # return orders, sum(sell_cnt_list)
                    break

                elif isinstance(revised_order, float):
                    """需要卖出的数量大于一笔买单的数量，需要对第二条买单数量进行判断"""
                    # print(2)
                    sell_cnt_list.append(order.buy_cnt)
                    selling_cnt = revised_order

                else:
                    # print(3)
                    """需要卖出的数量小于一笔买单的数量，需要拆分订单"""
                    order_list1 = orders[:i+1]
                    order_list2 = orders[i+1:]

                    order_list1.append(revised_order)

                    sell_cnt_list.append(order.sell_cnt)
                    orders = order_list1 + order_list2
                    # return orders, sum(sell_cnt_list)
                    break

        return orders, sum(sell_cnt_list)
        # return revised_order_list, sum(sell_cnt_list)

    def sell_tomorrow_order(self, order, holding_cnt, selling_cnt, orders_list):
        """
        针对卖出数量与买入数量不等的情况下，生成新订单的进一步封装，应用于具体的卖出策略当中
        :param order: 生成的交易订单AbuOrder对象
        :param holding_cnt: 卖出交易发生时的持仓量
        :param selling_cnt: 卖出交易量
        :param orders_list: 存放新生成的订单列表
        """
        revised_order = self.sell_tomorrow(order, holding_cnt, selling_cnt)
        if revised_order is not None:
            orders_list.append(revised_order)

        return orders_list

    def sell_tomorrow(self, order, holding_cnt, selling_cnt):
        """
        明天进行卖出操作，比如突破策略使用了今天收盘的价格做为参数，发出了买入信号，
        需要进行卖出操作，不能执行今天卖出操作
        :param order交易订单AbuOrder对象
        :param holding_cnt: 卖出交易发生时的持仓量
        :param selling_cnt: 卖出交易量
        """
        return self.revise_sell_order(order.fit_sell_order(self.today_ind, holding_cnt, selling_cnt, self))

    def sell_today(self, order, holding_cnt):
        """
        今天即进行卖出操作，需要不能使用今天的收盘数据等做为fit_day中信号判断，
        适合如比特币非明确一天交易日时间或者特殊情况的卖出信号
        :param order交易订单AbuOrder对象
        :param holding_cnt: 卖出交易发生时的持仓量
        """
        return self.revise_sell_order(order.fit_sell_order(self.today_ind - 1, holding_cnt, self))

    # noinspection PyMethodMayBeStatic
    def revise_sell_order(self, order):
        """
        对新生成的卖单进行修正，即如果卖出数量小于买入数量，将原订单进行修改，并生成一条新的买单
        :param order: order交易订单AbuOrder对象
        :return: 新生成的买单
        """

        # holding_cnt = order.buy_cnt - order.sell_cnt

        if order is None:
            return

        if order.sell_cnt == 0:
            return

        else:
            holding_cnt = order.buy_cnt - order.sell_cnt

            if holding_cnt == 0:
                """单笔卖出恰好等于买入数量"""
                return ''

            elif holding_cnt < 0:
                """单笔卖出大于买入数量"""
                order.sell_cnt = order.buy_cnt
                return -holding_cnt

            else:
                print('$$$$$')
                print()
                order.buy_cnt = order.sell_cnt
                new_order = deepcopy(order)

                # 初始化订单信息
                new_order.buy_cnt = holding_cnt
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

                # 订单买入，卖出特征
                new_order.ml_features = None
                # 订单形成
                new_order.order_deal = True

                return new_order

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

    # noinspection PyMethodMayBeStatic
    def sell_cnt_calc(self, today, order, sell_cnt_list):
        """过滤掉之前已经成交的卖单，避免重复计算平仓量"""

        if order.sell_type != 'keep' and order.sell_date > today.date:
            # 保证外部不需要过滤单子，内部自己过滤已经卖出成交的订单
            return sell_cnt_list.append(order.sell_cnt)

        else:
            return sell_cnt_list

    @abstractmethod
    def _init_self(self, **kwargs):
        """子类因子针对可扩展参数的初始化"""
        pass

    @abstractmethod
    def fit_day(self, today, holding_cnt, orders):
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


class AbuFactorSellXD(AbuFactorSellBase):
    """以周期为重要参数的策略，xd代表参数'多少天'如已周期为参数可直接继承使用 """

    def _init_self(self, **kwargs):
        """kwargs中必须包含: 突破参数xd 比如20，30，40天...突破"""
        # 向下突破参数 xd， 比如20，30，40天...突破
        self.xd = kwargs['xd']
        # 在输出生成的orders_pd中显示的名字
        self.sell_type_extra = '{}:{}'.format(self.__class__.__name__, self.xd)

    def read_fit_day(self, today, orders):
        """
        覆盖base函数, 为fit_day中切片周期金融时间序列数据
        :param today: 当前驱动的交易日金融时间序列数据
        :param orders: 买入择时策略中生成的订单序列
        :return: 生成的交易订单AbuOrder对象
        """
        # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.key)
        # 回测中默认忽略最后一个交易日
        if self.today_ind >= self.kl_pd.shape[0] - 1:
            return
        orders = list(filter(lambda order: order.expect_direction in self.support_direction(), orders))

        # 完成为fit_day中切片周期金融时间序列数据
        self.xd_kl = self.kl_pd[self.today_ind - self.xd + 1:self.today_ind + 1]

        return self.fit_day(today, orders)

    def support_direction(self):
        """raise NotImplementedError"""
        raise NotImplementedError('NotImplementedError support_direction')

    def fit_day(self, today, orders):
        """raise NotImplementedError"""
        raise NotImplementedError('NotImplementedError fit_day')
