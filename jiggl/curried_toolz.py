"""

If you do:
>>> from toolz import curried as toolz

Toolz dynamically curries any applicable functions, and adds them to the
locals dict. This is problem for PyCharm's static code analysis.

This stops PyCharm from freaking out by creating a file where
all of the curryable functions are manually curried.

"""
import os
current_path = os.path.dirname(os.path.realpath(__file__))
out_fname = os.path.join(current_path, '_curried_toolz.py')

if not os.path.isfile(out_fname):

    def update_file():
        print 'Creating a nice static file for pycharm'
        import toolz
        from toolz.curried import _d, _exceptions
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO

        buff = StringIO()
        buff.write('from toolz import *\n\n')
        funcs = sorted(toolz.merge(_d, _exceptions).items())

        curried_names = [name for name, f in funcs if isinstance(f, toolz.curry)]

        for name in curried_names:
            buff.write('%(name)s = curry(%(name)s)\n' % {'name': name})

        with open(out_fname, 'w') as f:
            f.write(buff.getvalue())

    update_file()
    for l in ['update_file', 'current_path', 'out_fname']:
        del locals()[l]

from _curried_toolz import *