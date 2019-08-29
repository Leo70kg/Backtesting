# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt


def show_factor_with_ret(factor_df, subplots=False):
    """
    可视化因子序列与收益率序列
    :param factor_df: 可为多个因子序列，dataFrame对象
    :param subplots: 是否根据factor_df中的每列单独做图
    :return:
    """
    # noinspection PyTypeChecker
    factor_df[factor_df.columns].plot(subplots=subplots, figsize=(16, 12), grid=True)
    plt.show()

