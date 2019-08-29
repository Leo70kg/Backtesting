# -*- coding: utf-8 -*-
# Leo70kg
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


def dsi(ret):
    return sum(ret) / sum(abs(ret))


def rsi(ret):
    return float((ret > 0).sum()) / float(len(ret))

