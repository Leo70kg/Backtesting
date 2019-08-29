cimport scipy.special.cython_special as cs
from libc.math cimport sqrt, log, exp
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double _day_to_year(double a, double trade_calendar):
    cdef double c
    if trade_calendar:
        c = a / 252
    else:
        c = a / 365
    return c


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double _hour_to_year(double a, double trade_calendar):
    cdef double c
    if trade_calendar:
        c = a / 6 / 252
    else:
        c = a / 24 / 365
    return c


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double d_one(double s, double k, double r, double q, double t, double v):
    cdef double c1, c2
    cdef double result

    c1 = log(s / k) + (0.5 * v * v + r - q) * t
    c2 = v * sqrt(t)

    if c2 == 0:
        result = 0
    else:
        result = (log(s / k) + (0.5 * v * v + r - q) * t) / (v * sqrt(t))
    return result


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double bs_price(double s, double k, double r, double q, double t, double v, double cp):
    cdef double d1
    cdef double d2
    cdef double price

    if t == 0:
        price = 0
    else:
        d1 = d_one(s, k, r, q, t, v)
        d2 = d1 - v * sqrt(t)
        price = cp * (s * exp(-q * t) * cs.ndtr(cp * d1) - k * exp(-r * t) * cs.ndtr(cp * d2))

    return price


@cython.boundscheck(False)
@cython.wraparound(False)
cdef double bs_delta(double s, double k, double r, double q, double t, double v, double cp):
    cdef double d1
    cdef double d2
    cdef double delta

    if t == 0:
        delta = 0
    else:
        d1 = d_one(s, k, r, q, t, v)
        d2 = d1 - v * sqrt(t)
        delta = cp * cs.ndtr(cp * d1) * exp(-q * t)

    return delta


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int _to_date_int(int year, int month, int day):
    cdef int result
    result = year * 10000 + month * 100 + day

    return result


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* date_split(int date):
    cdef int year
    cdef int month
    cdef int day
    cdef int arr[3]

    year = date / 10000
    month = date % 10000 / 100
    day = date % 100

    arr[0] = year
    arr[1] = month
    arr[2] = day

    return arr

# ----------------------------------------------------------------------
def convert_day_to_year(t, trade_calendar):
    return _day_to_year(t, trade_calendar)


def convert_hour_to_year(t, trade_calendar):
    return _hour_to_year(t, trade_calendar)


def split_date_int(date):
    result = date_split(date)
    return result[0], result[1], result[2]


def to_date_int(year, month, day):
    return _to_date_int(year, month, day)


def delta(s, k, r, q, t, v, cp):
    return bs_delta(s, k, r, q, t, v, cp)


def price(s, k, r, q, t, v, cp):
    return bs_price(s, k, r, q, t, v, cp)