# -*- encoding:utf-8 -*-
"""
    期货买入择时策略因子基础模块
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import copy
from abc import ABCMeta, abstractmethod

from ..CoreBu.ABuFixes import six
from ..CoreBu.ABuDeprecated import AbuDeprecated
from ..CoreBu.ABuEnv import g_futures_cn_date_dict
from ..DataHandlerBu import AbuDataHandler
from ..BetaBu.ABuAtrPosition import AbuAtrPosition
from ..BetaBu import ABuPositionBase
from ..TradeBu.ABuOrder import AbuOrder
from ..TradeBu.ABuMLFeature import AbuMlFeature
from ..CoreBu.ABuBase import AbuParamBase
from ..SlippageBu.ABuSlippageBuyMean import AbuSlippageBuyMean
from ..SlippageBu.ABuSlippageBuyCallTick import AbuSlippageBuyCallTick
from ..UtilBu.ABuLazyUtil import LazyFunc
from ..UmpBu.ABuUmpManager import AbuUmpManager
from ..UtilBu.ABuDateUtil import get_minute_from_numpy_datetime64 as get_min
from ..UtilBu.ABuDateUtil import get_hour_from_numpy_datetime64 as get_hour
from ..UtilBu.ABuStrUtil import get_letters


class BuyCallMixin(object):
    """
        混入类，混入代表买涨，不完全是期权中buy call的概念，
        只代表看涨正向操作，即期望买入后交易目标价格上涨，上涨带来收益
    """

    @LazyFunc
    def buy_type_str(self):
        """用来区别买入类型unique 值为call"""
        return "call"

    @LazyFunc
    def expect_direction(self):
        """期望收益方向，1.0即正向期望"""
        return 1.0


class BuyPutMixin(object):
    """
        混入类，混入代表买跌，应用场景在于期权，期货策略中，
        不完全是期权中buy put的概念，只代看跌反向操作，
        即期望买入后交易目标价格下跌，下跌带来收益
    """

    @LazyFunc
    def buy_type_str(self):
        """用来区别买入类型unique 值为put"""
        return "put"

    @LazyFunc
    def expect_direction(self):
        """期望收益方向，1.0即反向期望"""
        return -1.0


class AbuFactorBuyFuturesBase(six.with_metaclass(ABCMeta, AbuParamBase)):
    """
        买入择时策略因子基类：每一个继承AbuFactorBuyBase的子类必须混入一个方向类，
        且只能混入一个方向类，即具体买入因子必须明确买入方向，且只能有一个买入方向，
        一个因子不能同上又看涨又看跌，

        买入因子内部可容纳专属卖出因子和选股因子，即值针对本源生效的卖出因子和选股策略，
        且选股因子动态在择时周期内每月或者每周根据策略重新进行选股。
    """

    def __init__(self, capital, kl_pd, kl_pd_dict, benchmark, **kwargs):
        """
        :param capital:资金类AbuCapital实例化对象
        :param kl_pd:择时时段金融时间序列，pd.DataFrame对象
        :param kl_pd_dict:用于存储不同的频率下行情数据，dict对象
        :param benchmark: 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        """
        # 择时金融时间序列走势数据
        self.kl_pd = kl_pd
        # 机器学习特征数据构建需要，详情见make_buy_order_ml_feature中构造特征使用
        self.kl_pd_dict = kl_pd_dict
        # 资金情况数据
        self.capital = capital
        # 交易基准对象，AbuBenchmark实例对象, 因子可有选择性使用，比如大盘对比等功能
        self.benchmark = benchmark
        # 滑点类，默认AbuSlippageBuyMean
        self._slippage_class_init(**kwargs)
        # 仓位管理，默认AbuAtrPosition
        self._position_class_init(**kwargs)
        # 是否包含专属卖出因子
        self.if_attached = self._attached_sell_factors(**kwargs)
        # 构造ump对外的接口对象UmpManager
        self.ump_manger = AbuUmpManager(self)
        # 默认的factor_name，子类通过_init_self可覆盖更具体的名字
        self.factor_name = '{}'.format(self.__class__.__name__)
        # 忽略的交易日数量
        self.skip_days = 0
        # 是否封锁本源择时买入因子的执行，此值只通过本源择时买入因子附属的选股因子进行改变
        self.lock_factor = False
        # kwargs参数中其它设置赋予买入因子的参数
        self._other_kwargs_init(**kwargs)
        # 子类继续完成自有的构造
        self._init_self(**kwargs)
        # 买入因子持仓量
        self.holding_cnt = 0

    def _position_class_init(self, **kwargs):
        """仓位管理类构建"""

        # 仓位管理，默认AbuAtrPosition
        if ABuPositionBase.g_default_pos_class is None:
            self.position_class = AbuAtrPosition
            # 仓位管理类构建关键字参数默认空字典
            self.position_kwargs = dict()
        else:
            # 否则设置了全局仓位管理字典对象，弹出class
            default_pos_class = copy.deepcopy(ABuPositionBase.g_default_pos_class)
            self.position_class = default_pos_class.pop('class')
            # 弹出class后剩下的就为其它关键字参数
            self.position_kwargs = default_pos_class

        if 'position' in kwargs:
            position = kwargs.pop('position', AbuAtrPosition)
            if isinstance(position, six.class_types):
                # 如果position里面直接设置的是一个class，直接弹出
                self.position_class = position
            elif isinstance(position, dict):
                # 支持赋予字典结构 eg: {'class': AbuAtrPosition, 'atr_base_price': 20, 'atr_pos_base': 0.5}
                if 'class' not in position:
                    # 必须要有需要实例化的类信息
                    raise ValueError('position class key must name class !!!')
                position_cp = copy.deepcopy(position)
                # pop出类信息后剩下的都为类需要的参数
                self.position_class = position_cp.pop('class')
                # pop出class之后剩下的就class的构造关键字参数
                self.position_kwargs = position_cp
            else:
                raise TypeError('_position_class_init position type is {}'.format(type(position)))

    def _slippage_class_init(self, **kwargs):
        """滑点类构建"""
        # 滑点类，默认AbuSlippageBuyMean
        self.slippage_class = kwargs.pop('slippage', AbuSlippageBuyCallTick)
        # TODO 滑点类完善参数构建等需求

    def _attached_sell_factors(self, **kwargs):
        """判断是否含有专属卖出因子"""
        result = 'sell_factors' in kwargs
        return result

    def _other_kwargs_init(self, **kwargs):
        """
            kwargs参数中其它设置赋予买入因子的参数：
            可选参数win_rate：策略因子期望胜率（可根据历史回测结果计算得出）
            可选参数gains_mean：策略因子期望收益（可根据历史回测结果计算得出）
            可选参数gains_mean：策略因子期望亏损（可根据历史回测结果计算得出）

            可选参数stock_pickers：专属买入择时策略因子的选股因子序列，序列中对象为选股因子
            可选参数sell_factors： 专属买入择时策略因子的择时卖出因子序列，序列中对象为卖出因子
        """

        # # 先处理过时的方法
        # self._deprecated_kwargs_init(**kwargs)
        #
        # # 专属买入策略因子的选股周生效因子
        # self.ps_week = []
        # # 专属买入策略因子的选股月生效因子
        # self.ps_month = []
        # # 专属买入策略因子的选股日生效因子
        # self.ps_day = []
        # # 专属买入策略因子的选股因子
        # stock_pickers = kwargs.pop('stock_pickers', [])
        # for picker_class in stock_pickers:
        #     if picker_class is None:
        #         continue
        #     if 'class' not in picker_class:
        #         # 必须要有需要实例化的类信息
        #         raise ValueError('picker_class class key must name class !!!')
        #     picker_class_cp = copy.deepcopy(picker_class)
        #     # pop出类信息后剩下的都为类需要的参数
        #     class_fac = picker_class_cp.pop('class')
        #     # 专属买入策略因子独有可设置选股因子生效周期，默认一个月重新进行一次选股，设置week为一周
        #     pick_period = picker_class_cp.pop('pick_period', 'month')
        #     # 整合capital，benchmark等实例化因子对象
        #     picker = class_fac(self.capital, self.benchmark, **picker_class_cp)
        #     if pick_period == 'month':
        #         self.ps_month.append(picker)
        #     elif pick_period == 'week':
        #         self.ps_week.append(picker)
        #     else:
        #         self.ps_day.append(picker)
        #         # raise ValueError('pick_period just support month|week!')

        # 专属买入策略因子的卖出因子策略，只针对本源择时买入因子生效
        self.sell_factors = []
        sell_factors = kwargs.pop('sell_factors', [])
        for factor_class in sell_factors:
            if factor_class is None:
                continue
            if 'class' not in factor_class:
                # 必须要有需要实例化的类信息
                raise ValueError('factor class key must name class !!!')
            factor_class_cp = copy.deepcopy(factor_class)
            # pop出类信息后剩下的都为类需要的参数
            class_fac = factor_class_cp.pop('class')
            # 整合capital，kl_pd等实例化因子对象
            factor = class_fac(self.capital, self.kl_pd, self.kl_pd_dict, self.benchmark, **factor_class_cp)
            # 添加到本源卖出因子序列
            self.sell_factors.append(factor)

    def __str__(self):
        """打印对象显示：class name, slippage, position, kl_pd.info"""
        return '{}: slippage:{}, position:{} \nkl:\n{}'.format(self.__class__.__name__,
                                                               self.slippage_class, self.position_class,
                                                               self.kl_pd.info())

    __repr__ = __str__

    def make_buy_order(self, holding_object, day_ind=-1):
        """
        根据交易发生的时间索引，依次进行交易订单生成，交易时间序列特征生成，
        决策交易是否拦截，生成特征学习数据，最终返回order，即订单生效
        :param holding_object: 交易发生之前的持仓量
        :param day_ind: 交易发生的时间索引，即对应self.kl_pd.key
        """
        if day_ind == -1:
            # 默认模式下非高频，信号发出后，明天进行买入操作
            day_ind = self.today_ind

        order = AbuOrder()
        # AbuOrder对象根据交易发生的时间索引生成交易订单
        order.fit_buy_order(day_ind, holding_object, self)

        # if order.order_deal:
        #     # 交易时间序列特征生成
        #     ml_feature_dict = self.make_buy_order_ml_feature(day_ind)
        #     # 决策交易是否被ump拦截还是可以放行
        #     block = self.make_ump_block_decision(ml_feature_dict)
        #     if block:
        #         return None
        #
        #     # 如果交易即将成交，将生成的交易特征写入order的特征字段ml_features中，为之后使用机器学习计算学习特征，训练ump
        #     if order.ml_features is None:
        #         order.ml_features = ml_feature_dict
        #     else:
        #         order.ml_features.update(ml_feature_dict)
        # 返回order，订单生效
        return order

    def make_ump_block_decision(self, ml_feature_dict):
        """
        输入需要决策的当前买入交易特征通过ump模块的对外manager对交易进行决策，
        判断是否拦截买入交易，还是放行买入交易。子类可复写此方法，即子类策略因子实现
        自己的任意ump组合拦截方式，根据策略的拦截比例需要等等参数确定ump具体策略，
        且对于多种策略并行执行策略本身定制适合自己的拦截策略，提高灵活度
        :param ml_feature_dict: 需要决策的当前买入时刻交易特征dict
        :return: bool, 对ml_feature_dict所描述的交易特征是否进行拦截
        """
        return self.ump_manger.ump_block(ml_feature_dict)

    def make_buy_order_ml_feature(self, day_ind):
        """
        根据交易发生的时间索引构通过AbuMlFeature构建买入时刻的各个交易特征
        :param day_ind: 交易发生的时间索引，对应self.kl_pd.key
        :return:
        """
        return AbuMlFeature().make_feature_dict(self.kl_pd, self.combine_kl_pd, day_ind, buy_feature=True)

    @abstractmethod
    def _init_self(self, **kwargs):
        """子类因子针对可扩展参数的初始化"""
        pass

    def read_fit_day(self, today, holding_object):
        """
        在择时worker对象中做日交易的函数，亦可以理解为盘前的一些决策事件处理，
        内部会调用子类实现的fit_day函数
        :param today: 当前驱动的交易日金融时间序列数据
        :param holding_object: 交易发生之前的持仓量
        :return: 生成的交易订单AbuOrder对象
        """

        # if self.skip_days > 0:
        #     self.skip_days -= 1
        #     return None, None
        #
        # # 今天这个交易日在整个金融时间序列的序号
        self.today_ind = int(today.values[14])
        # # 回测中默认忽略最后一个交易日
        # if self.today_ind >= self.kl_pd.shape[0] - 1:
        #     return None, None

        return self.fit_day(today, holding_object)

    def buy_tomorrow(self, holding_object):
        """
        明天进行买入操作，比如突破策略使用了今天收盘的价格做为参数，发出了买入信号，
        需要进行明天买入操作，不能执行今天买入操作
        :param holding_object: 交易发生之前的持仓量
        :return 生成的交易订单AbuOrder对象
        """
        return self.make_buy_order(holding_object, self.today_ind)

    def buy_today(self, holding_object):
        """
        今天即进行买入操作，需要不能使用今天的收盘数据等做为fit_day中信号判断，
        适合如比特币非明确一天交易日时间或者特殊情况的买入信号
        :param holding_object: 交易发生之前的持仓量
        :return 生成的交易订单AbuOrder对象
        """
        return self.make_buy_order(holding_object, self.today_ind - 1)

    # noinspection PyMethodMayBeStatic
    def get_freq_kl_pd(self, kl_pd, freq, kl_pd_dict):
        """
        根据一分钟k线行情获取特定频率周期下的k线行情，并输出该周期线每日k线数量
        :param kl_pd: 原始一分钟k线行情
        :param freq: 周期频率
        :param kl_pd_dict: 之前已保存在字典中的行情数据，目的为提高效率
        :return:
        """
        freq_kl_pd, kline_num = kl_pd_dict.get(freq, (None, None))

        if freq_kl_pd is None:
            freq_kl_pd, kline_num = AbuDataHandler.handle_kline(kl_pd, freq, kl_pd.name)
            kl_pd_dict[freq] = (freq_kl_pd, kline_num)

        return freq_kl_pd, kline_num

    # noinspection PyMethodMayBeStatic
    def get_contract_start_and_end_date(self, symbol):
        """
        获取该期货合约作为主力合约的起始日和终止日期
        :param symbol: 合约代码，str格式
        """
        start_date = g_futures_cn_date_dict[symbol][0]
        end_date = g_futures_cn_date_dict[symbol][1]

        return start_date, end_date

    # noinspection PyMethodMayBeStatic
    def get_freq_kl_pd_time_str(self, freq):
        """基础数据为每分钟k线，进行每分钟迭代时，在不同频率周期下，得到需要用到的字段名称，‘date’或者‘datetime’ """

        time_str = 'date' if get_letters(freq) == 'D' else 'revised_datetime'

        return time_str

    # noinspection PyMethodMayBeStatic
    def get_today_time_str_idx(self, freq):
        """基础数据为每分钟k线，进行每分钟迭代时，在不同频率周期下，得到需要用到的字段名称，‘date’或者‘resampled_datetime’ """

        # time_str = 'date' if get_letters(freq) == 'D' else freq + '_resampled_datetime'
        time_str_idx = 9 if get_letters(freq) == 'D' else 15

        return time_str_idx

    # noinspection PyMethodMayBeStatic
    def check_dominant_today(self, today_date, start_date, end_date):
        """
        针对期货合约回测，如果当前合约不处于主力合约有效期内，则不构成买单
        :param today_date: 当前驱动的交易日金融时间序列数据
        :param start_date: 主力合约生效的开始日期
        :param end_date: 主力合约生效的结束日期
        :return:
        """
        if today_date > end_date or today_date < start_date:
            return True
        else:
            return False

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

    def _fit_pick_stock(self, today, pick_array):
        """买入因子专属选股因子执行，只要一个选股因子发出没有选中的信号，就封锁本源择时因子"""

        for picker in pick_array:
            pick_kl = self.past_today_kl(today, picker.xd)

            if pick_kl.empty or not picker.fit_pick(pick_kl, self.kl_pd.name):
                # 只要一个选股因子发出没有选中的信号，就封锁本源选股因子
                self.lock_factor = True
                return
            # 遍历所有专属选股因子后，都没有发出封锁因子信号，就打开因子
            self.lock_factor = False

    def fit_ps_week(self, today):
        """买入因子专属'周'选股因子执行，只要一个选股因子发出没有选中的信号，就封锁本源择时因子"""
        self._fit_pick_stock(today, self.ps_week)

    def fit_ps_month(self, today):
        """买入因子专属'月'选股因子执行，只要一个选股因子发出没有选中的信号，就封锁本源择时因子"""
        self._fit_pick_stock(today, self.ps_month)

    def fit_ps_day(self, today):
        """买入因子专属'日'选股因子执行，只要一个选股因子发出没有选中的信号，就封锁本源择时因子"""
        self._fit_pick_stock(today, self.ps_day)

    @abstractmethod
    def fit_day(self, today, holding_object):
        """子类主要需要实现的函数，完成策略因子针对每一个交易日的买入交易策略"""
        pass

    def past_today_kl(self, today, past_day_cnt):
        """
            在fit_day, fit_month, fit_week等时间驱动经过的函数中通过传递今天的数据
            获取过去past_day_cnt天的交易日数据，返回为pd.DataFrame数据
            :param today: 当前驱动的交易日金融时间序列数据
            :param past_day_cnt: int，获取今天之前过去past_day_cnt天的金融时间序列数据
        """
        end_ind = self.combine_kl_pd[self.combine_kl_pd.date == today.date].key.values[0]
        start_ind = end_ind - past_day_cnt if end_ind - past_day_cnt > 0 else 0
        # 根据当前的交易日，切片过去一段时间金融时间序列
        return self.combine_kl_pd.iloc[start_ind:end_ind+1]

    def past_today_one_month(self, today):
        """套接past_today_kl，获取今天之前1个月交易日的金融时间序列数据"""
        # TODO 这里固定了值，最好使用env中的时间，如币类市场等特殊情况
        return self.past_today_kl(today, 20)

    def past_today_one_week(self, today):
        """套接past_today_kl，获取今天之前1周交易日的金融时间序列数据"""
        # TODO 这里固定了值，最好使用env中的时间，如币类市场等特殊情况
        return self.past_today_kl(today, 5)

    def past_today_one_year(self, today):
        """套接past_today_kl，获取今天之前1年交易日的金融时间序列数据"""
        # TODO 这里固定了值，最好使用env中的时间，如币类市场等特殊情况
        return self.past_today_kl(today, 250)

    def _deprecated_kwargs_init(self, **kwargs):
        """处理过时的初始化"""
        if 'win_rate' in kwargs and 'gains_mean' in kwargs and 'losses_mean' in kwargs:
            self._do_kelly_deprecated(**kwargs)

    @AbuDeprecated('kelly object now use dict to build, it will be remove next version!')
    def _do_kelly_deprecated(self, **kwargs):
        """针对kelly仓位管理过时方法的处理"""

        """
            因子可选择根据策略的历史回测设置胜率，期望收益，期望亏损，
            比如使用AbuKellyPosition，必须需要因子的胜率，期望收益，
            期望亏损参数，不要使用kwargs.pop('a', None)设置，因为
            暂时使用hasattr判断是否有设置属性
        """
        # 策略因子历史胜率win_rate, 策略因子历史期望收益gains_mean, 策略因子历史期望亏损losses_mean
        self.position_kwargs = {'win_rate': kwargs['win_rate'], 'gains_mean': kwargs['gains_mean'],
                                'losses_mean': kwargs['losses_mean']}

    """TODO: 使用check support方式查询是否支持fit_week，fit_month，上层不再使用hasattr去判断"""
    # def fit_week(self, *args, **kwargs):
    #     pass

    # def fit_month(self, *args, **kwargs):
    #     pass
