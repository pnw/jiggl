# http://www.dustingetz.com/2012/04/07/dustins-awesome-monad-tutorial-for-humans-in-python.html
import functools


def success(val):
    return val, None


def error(val, why):
    return val, why


def get_val(m_val):
    return m_val[0]


def get_error(m_val):
    return m_val[1]


def has_error(m_val):
    return bool(get_error(m_val))


def has_no_error(m_val):
    return not has_error(m_val)


def unit(value):
    return value, None


def bind(mf, mval):
    return mf(get_val(mval)) if not get_error(mval) else mval


def compose(*functions):
    """
    Functional composition
    https://mathieularose.com/function-composition-in-python/
    """
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
