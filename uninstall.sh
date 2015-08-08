#!/usr/bin/env bash

# uninstalls all of the files created by `python setup.py install`
rm -r $VIRTUAL_ENV/bin/jigg*
rm -r $VIRTUAL_ENV/lib/python2.7/site-packages/jigg*