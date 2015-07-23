# http://www.dustingetz.com/2012/04/07/dustins-awesome-monad-tutorial-for-humans-in-python.html
from collections import namedtuple
import os
import toolz as z

M_Entry = namedtuple('M_Entry', ['value', 'error'])


def unit(val):
    return M_Entry(val, None)


def success(val):
    return M_Entry(val, None)


def error(val, why):
    return M_Entry(val, why)


def get_val(m_val):
    return m_val.value


def get_error(m_val):
    return m_val.error


def has_error(m_val):
    return bool(get_error(m_val))


def has_no_error(m_val):
    return not has_error(m_val)


@z.curry
def bind(mf, mval):
    return mf(get_val(mval)) if not get_error(mval) else mval


def clear_screen():
    """Simply clears the screen"""
    os.system(['clear', 'cls'][os.name == 'nt'])
