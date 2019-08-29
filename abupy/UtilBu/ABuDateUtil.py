# -*- encoding:utf-8 -*-
"""
    时间日期工具模块
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import datetime
import time
import math
from datetime import datetime as dt
from datetime import date

from ..CoreBu.ABuEnv import g_trade_date_list, g_hour_dict
from ..CoreBu.ABuFixes import six
# noinspection PyUnresolvedReferences
from ..CoreBu.ABuFixes import filter

try:
    # 如果有安装dateutil使用relativedelta as timedelta
    from dateutil.relativedelta import relativedelta as timedelta
except ImportError:
    # 没有安装dateutil使用datetime.timedelta
    from datetime import timedelta


__author__ = '阿布'
__weixin__ = 'abu_quant'


"""默认的时间日期格式，项目中金融时间序列等时间相关默认格式"""
K_DEFAULT_DT_FMT = "%Y-%m-%d"


def get_start(n_folds, start, end):
    """
    根据给定的回测周期n_folds，获取回测初始日期，若给定初始日期，则直接输出
    :param n_folds: 回测周期，以年记
    :param start: 初始日期，可为字符串或None
    :param end: 截止日期，可为字符串或None
    :return:
    """
    today = current_str_date()
    if end is None:
        # 没有end也没start，end＝today，否则使用n_folds计算end
        end = today if start is None else begin_date(-math.floor(365 * n_folds), date_str=start, fix=False)
        end_int = date_str_to_int(end)
        today_int = date_str_to_int(today)
        if end_int > today_int:
            end = today

    if start is None:
        start = begin_date(math.floor(365 * n_folds), date_str=end, fix=False)

    return str_to_date_fast(start), str_to_date_fast(end)


def str_to_datetime(date_str, fmt=K_DEFAULT_DT_FMT, fix=True):
    """
    将字符串日期格式转换成datetime.datetime对象 eg. '2016-01-01' －> datetime.datetime(2016, 1, 1, 0, 0)
    :param date_str: %Y-%m-%d 形式str对象，eg. '2016-01-01'
    :param fmt: 如date_str不是%Y-%m-%d形式，对应的格式str对象
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: datetime.datetime对象，eg. datetime.datetime(2016, 1, 1, 0, 0)
    """
    if fix and fmt == K_DEFAULT_DT_FMT:
        # 只针对%Y-%m-%d形式格式标准化日期格式
        date_str = fix_date(date_str)

    return dt.strptime(date_str, fmt)


def str_to_datetime_fast(date_str, split='-', fix=True):
    """
    不使用datetime api直接进行字符串分解，相对str_to_datetime要快很多，大概2倍的时间，大量时间转换，且格式确定使用
    将字符串日期格式转换成datetime.datetime对象 eg. '2016-01-01' －> datetime.datetime(2016, 1, 1, 0, 0)
    :param date_str: 如date_str不是%Y-%m-%d形式，对应的格式str对象
    :param split: 年月日的分割符，默认'-'
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: datetime.datetime对象，eg. datetime.datetime(2016, 1, 1, 0, 0)
    """
    if fix and split == '-':
        # 只针对%Y-%m-%d形式格式标准化日期格式
        date_str = fix_date(date_str)
    y, m, d = date_str.split(split)
    return dt(int(y), int(m), int(d))


def int_to_datetime(date_int):

    year = round(date_int / 10000)
    month = round(date_int % 10000 / 100)
    day = date_int % 100

    return datetime.datetime(year, month, day)


def str_to_date_fast(date_str, split='-', fix=True):
    """
    格式确定使用
    将字符串日期格式转换成datetime.date对象 eg. '2016-01-01' －> datetime.datetime(2016, 1, 1, 0, 0)
    :param date_str: 如date_str不是%Y-%m-%d形式，对应的格式str对象
    :param split: 年月日的分割符，默认'-'
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: datetime.date对象，eg. datetime.date(2016, 1, 1)
    """

    if fix and split == '-':
        # 只针对%Y-%m-%d形式格式标准化日期格式
        date_str = fix_date(date_str)
    y, m, d = date_str.split(split)
    return date(int(y), int(m), int(d))


def datetime_to_str(dt_obj):
    """
    datetime时间转换为str对象, str_to_datetime函数的逆向
    :param dt_obj: datetime.datetime对象
    :return: str对象 eg. '2016-01-01'
    """
    return str(dt_obj.date())[:10]


def timestamp_to_str(ts):
    """
    针对pandas.tslib.Timestamp对象，即金融时间序列index元素对象转换为str对象, 时间单位只取到天，返回如2016-01－01
    :param ts: pandas.tslib.Timestamp对象，eg. Timestamp('2016-01-01 00:00:00')
    :return: 回如2016-01－01 str对象
    """
    try:
        # pandas高版本to_pydatetime
        s_date = str(ts.to_pydatetime().date())[:10]
    except:
        # pandas低版本to_datetime
        s_date = str(ts.to_datetime().date())[:10]
    return s_date


def date_str_to_int(date_str, split='-', fix=True):
    """
    eg. 2016-01-01 -> 20160101
    不使用时间api，直接进行字符串解析，执行效率高
    :param date_str: %Y-%m-%d形式时间str对象
    :param split: 年月日的分割符，默认'-'
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: int类型时间
    """
    if fix and split == '-':
        # 只针对%Y-%m-%d形式格式标准化日期格式
        date_str = fix_date(date_str)
    string_date = date_str.replace(split, '')
    return int(string_date)


def datetime_str_to_int(datetime_str):
    """
    eg. 2016-10-10 09:01:00 -> 20161010090100
    :param datetime_str:
    :return: int类型
    """

    date_str, time_str = datetime_str.split(' ')
    str_date = date_str.replace('-', '')
    # str_time = time_str.replace(':', '')

    return int(str_date)


def fix_date(date_str):
    """
    修复日期不规范的写法:
                eg. 2016-1-1 fix 2016-01-01
                eg. 2016:01-01 fix 2016-01-01
                eg. 2016,01 01 fix 2016-01-01
                eg. 2016/01-01 fix 2016-01-01
                eg. 2016/01/01 fix 2016-01-01
                eg. 2016/1/1 fix 2016-01-01
                eg. 2016:1:1 fix 2016-01-01
                eg. 2016 1 1 fix 2016-01-01
                eg. 2016 01 01 fix 2016-01-01
                .............................
    不使用时间api，直接进行字符串解析，执行效率高，注意fix_date内部会使用fmt_date
    :param date_str: 检测需要修复的日期str对象或者int对象
    :return: 修复了的日期str对象
    """
    if date_str is not None:
        # 如果是字符串先统一把除了数字之外的都干掉，变成干净的数字串
        if isinstance(date_str, six.string_types):
            # eg, 2016:01-01, 201601-01, 2016,01 01, 2016/01-01 -> 20160101
            date_str = ''.join(list(filter(lambda c: c.isdigit(), date_str)))
        # 再统一确定%Y-%m-%d形式
        date_str = fmt_date(date_str)
        y, m, d = date_str.split('-')
        if len(m) == 1:
            # 月上补0
            m = '0{}'.format(m)
        if len(d) == 1:
            # 日上补0
            d = '0{}'.format(d)
        date_str = "%s-%s-%s" % (y, m, d)
    return date_str


def fmt_date(convert_date):
    """
    将时间格式如20160101转换为2016-01-01日期格式, 注意没有对如 201611
    这样的做fix适配，外部需要明确知道参数的格式，针对特定格式，不使用时间api，
    直接进行字符串解析，执行效率高
    :param convert_date: 时间格式如20160101所示，int类型或者str类型对象
    :return: %Y-%m-%d日期格式str类型对象
    """
    if isinstance(convert_date, float):
        # float先转换int
        convert_date = int(convert_date)
    convert_date = str(convert_date)

    if len(convert_date) > 8 and convert_date.startswith('20'):
        # eg '20160310000000000'
        convert_date = convert_date[:8]

    if '-' not in convert_date:
        if len(convert_date) == 8:
            # 20160101 to 2016-01-01
            convert_date = "%s-%s-%s" % (convert_date[0:4],
                                         convert_date[4:6], convert_date[6:8])
        elif len(convert_date) == 6:
            # 201611 to 2016-01-01
            convert_date = "%s-0%s-0%s" % (convert_date[0:4],
                                           convert_date[4:5], convert_date[5:6])
        else:
            raise ValueError('fmt_date: convert_date fmt error {}'.format(convert_date))
    return convert_date


def diff(start_date, end_date, check_order=True):
    """
    对两个输入日期计算间隔的天数，如果check_order=False, str日期对象效率最高
    :param start_date: str对象或者int对象，如果check_order=True int对象效率最高
    :param end_date: str对象或者int对象，如果check_order=True int对象效率最高
    :param check_order: 是否纠正参数顺序是否放置正常，默认check
    :return:
    """

    # 首先进来的date都格式化，主要进行的是fix操作，不管是int还是str，这样20160101转换为2016-01-01日期格式
    start_date = fix_date(start_date)
    end_date = fix_date(end_date)

    if check_order and isinstance(start_date, six.string_types):
        # start_date字符串的日期格式转换为int
        start_date = date_str_to_int(start_date)

    if check_order and isinstance(end_date, six.string_types):
        # end_date字符串的日期格式转换为int
        end_date = date_str_to_int(end_date)

    # 是否纠正参数顺序是否放置正常，默认check
    if check_order and start_date > end_date:
        # start_date > end_date说明要换一下
        tmp = end_date
        end_date = start_date
        start_date = tmp

    # fmt_date，但在不需要纠正check_order的情况，这些就都不会执行
    if isinstance(start_date, int):
        # noinspection PyTypeChecker
        start_date = fmt_date(start_date)
    if isinstance(end_date, int):
        # noinspection PyTypeChecker
        end_date = fmt_date(end_date)

    # 在不需要纠正check_order的情况, 直接执行的是这里
    sd = str_to_datetime(start_date)
    ed = str_to_datetime(end_date)

    return (ed - sd).days


def current_date_int():
    """
    获取当前时间日期 int值
    不使用时间api，直接进行字符串解析，执行效率高
    :return: 日期int值
    """
    date_int = 0
    # 首先获取str
    today = current_str_date()
    # 手动比系统a时间pi快
    today_array = today.split("-")
    if len(today_array) == 3:
        date_int = int(today_array[0]) * 10000 + int(today_array[1]) * 100 + int(today_array[2])
    return date_int


def current_str_date():
    """
    获取当前时间日期，时间单位只取到天，返回如2016-01－01
    :return: 返回如2016-01－01 str对象
    """
    return str(datetime.date.today())


def week_of_date(date_str, fmt=K_DEFAULT_DT_FMT, fix=True):
    """
    输入'2016-01-01' 转换为星期几，返回int 0-6分别代表周一到周日
    :param date_str: 式时间日期str对象
    :param fmt: 如date_str不是%Y-%m-%d形式，对应的格式str对象
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: 返回int 0-6分别代表周一到周日
    """

    if fix and fmt == K_DEFAULT_DT_FMT:
        # 只针对%Y-%m-%d形式格式标准化日期格式
        date_str = fix_date(date_str)
    return dt.strptime(date_str, fmt).weekday()


def date_revise(date_index):
    """将期货夜盘数据对应的日期归属到第二天交易日"""

    dates_fmt = list(map(lambda date_timestamp: str(date_timestamp), date_index))
    dates_list = list(map(lambda date_str: date_str_to_int(date_str), dates_fmt))

    date_week_list = list(map(lambda x: week_of_date(str(x), '%Y%m%d'), dates_list))
    date_week_dict = {'0': 1, '1': 2, '2': 3, '3': 4, '4': 0}

    timestamp_list = list(map(lambda date_timestamp: time_to_timestamp(date_timestamp), date_index))

    for i in range(len(date_week_list)):

        date_ind = dates_list[i]
        week_ind = date_week_list[i]
        timestamp_ind = timestamp_list[i]

        # if week_ind == 5:
        #     dates_list[i] = dates_list[i-1]
        #     date_week_list[i] = date_week_list[i-1]

        if timestamp_ind > 75600:

            date_idx = g_trade_date_list.index(date_ind)

            dates_list[i] = g_trade_date_list[date_idx+1]

            date_week_list[i] = date_week_dict[str(week_ind)]

        if timestamp_ind < 32460:
            dates_list[i] = dates_list[i-1]
            date_week_list[i] = date_week_list[i-1]

    return dates_list, date_week_list


def time_to_timestamp(date_datetime):
    """
    输入 datetime.datetime(2018, 10, 28, 10, 21, 0) 转换为时间戳整数格式，返回int
    :param date_datetime: datetime.datetime格式
    :return:
    """

    if isinstance(date_datetime, dt):
        timestamp = date_datetime.hour * 3600 + date_datetime.minute * 60 + date_datetime.second * 60
        return timestamp


def begin_date(pre_days, date_str=None, split='-', fix=True):
    """
    返回date_str日期前pre_days天的日期str对象
        eg:
            pre_days = 2
            date_str = '2017-02-14'
            result = '2017-02-12'

            pre_days = 365
            date_str = '2016-01-01'
            result = '2015-01-01'

        如果pre_days是负数，则时间向前推：
        eg:
            pre_days = -365
            date_str = '2016-01-01'
            result = '2016-12-31'
    :param pre_days: pre_days天, int
    :param date_str: date_str, 默认current_str_date()
    :param split:
    :param fix: 是否修复日期不规范的写法，eg. 2016-1-1 fix 2016-01-01
    :return: str日期时间对象
    """

    if date_str is None:
        date_str = current_str_date()
        # 如果取current_str_date就没有必要fix了
        fix = False
    dt_time = str_to_datetime_fast(date_str, split=split, fix=fix)
    return str(dt_time + timedelta(days=-pre_days))[:10]


def time_seconds():
    """
    获取当前时间seconds级计时值
    :return:  float值 eg. 1498381468.38095
    """
    return time.time()


def time_zone():
    """返回时区int值"""
    return time.timezone


def get_minute_from_numpy_datetime64(dt64):
    """
    日内高频数据构建订单过程中，需要过滤掉不符合所选频率的行情数据，
    此函数为选取numpy.datetime64的日期格式中的分钟数，返回int格式
    :param dt64:
    :return:
    """
    return int(str(dt64)[14:16])


def get_hour_from_numpy_datetime64(dt64):

    return int(str(dt64)[11:13])


def get_hour_dict():
    """生成形如{'00':'01', '10':'11'}的字典，用于生成迭代后的特定频率时间"""
    hour_dic = {}
    for i in range(0, 24):
        if i == 23:
            hour_dic[str(i).zfill(2)] = '00'
        else:
            hour_dic[str(i).zfill(2)] = str(i+1).zfill(2)

    return hour_dic


# TODO 提高运行效率
def datetime_trans_to_resampled(str_datetime, date_ind, freq):
    """
    将str类型的datetime，在重采样周期下更新对应的datetime，
    比如，'2019-09-09 10:10:00' 在15分钟周期下对应的时间点是'2019-09-09 10:15:00'
    :param str_datetime: str类型
    :param date_ind: int类型
    :param freq: int类型
    :return:
    """
    hour = str_datetime[11:13]
    minute = int(str_datetime[14:16])
    n = minute / freq
    if minute % freq == 0:
        if int(hour) < 9:
            new_str_datetime = datetime_to_str(int_to_datetime(date_ind)) + str_datetime[10:]
            return new_str_datetime

        return str_datetime

    if n > (60 / freq - 1):

        new_min = '00'
        new_hour = g_hour_dict[hour]
        if int(new_hour) < 9:

            new_str_datetime = datetime_to_str(int_to_datetime(date_ind)) + ' ' + new_hour + ':00:00'

        else:
            new_str_datetime = str_datetime[:11] + new_hour + str_datetime[13:14] + new_min + str_datetime[16:]

    else:

        new_min = str(freq * (math.floor(n) + 1)).zfill(2)
        if int(hour) < 9:
            new_str_datetime = datetime_to_str(int_to_datetime(date_ind)) + ' ' + hour + ':' + new_min + \
                               str_datetime[16:]

        else:
            new_str_datetime = str_datetime[:14] + new_min + str_datetime[16:]

    return new_str_datetime


def resampled_df_revise(str_datetime, date_ind):
    """对根据特定频率合成的行情数据进行进一步整合，主要针对周五夜盘尤其是周六凌晨的数据点，将此时间规划到下一个交易日"""

    hour = int(str_datetime[11:13])
    date = datetime_str_to_int(str_datetime)

    if hour < 9:
        if date != date_ind:
            new_str_datetime = datetime_to_str(int_to_datetime(date_ind)) + str_datetime[10:]
            return new_str_datetime

    return str_datetime
