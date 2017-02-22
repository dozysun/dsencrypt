#!/usr/bin/env python2.7
# encoding:utf-8
# Created on 2017-02-20, by dozysun

#!/usr/bin/env python
# -*- coding:utf8 -*-
'''
Author : Myth
Date   : 16/7/7
Email  : belongmyth at 163.com
'''

import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from collections import defaultdict
import os
from optparse import OptionParser
import logging
import commands
from dsencrypt import encrypt_file
ENCRYPT = True

logger = None

ATTRIBUTES = dict(
    list(zip([
        'bold',
        'dark',
        '',
        'underline',
        'blink',
        '',
        'reverse',
        'concealed'
    ],
        list(range(1, 9))
    ))
)
del ATTRIBUTES['']

HIGHLIGHTS = dict(
    list(zip([
        'on_grey',
        'on_red',
        'on_green',
        'on_yellow',
        'on_blue',
        'on_magenta',
        'on_cyan',
        'on_white'
    ],
        list(range(40, 48))
    ))
)

COLORS = dict(
    list(zip([
        'grey',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white',
    ],
        list(range(30, 38))
    ))
)

RESET = '\033[0m'

IGNORE_FILES = [
    '/opt/scanner/src/scanner/celeryconfig.py',
    '/opt/proj/src/proj/gunicorn_config.py',
    '/opt/scanner/src/scanner/gunicorn_thrift_server/gunicorn_config.py',
    '/opt/scanner/src/scanner/plugins/BruteLogin/brute_login.py'
]


def colored(text, color=None, on_color=None, attrs=None):
    if os.getenv('ANSI_COLORS_DISABLED') is None:
        fmt_str = '\033[%dm%s'
        if color is not None:
            text = fmt_str % (COLORS[color], text)

        if on_color is not None:
            text = fmt_str % (HIGHLIGHTS[on_color], text)

        if attrs is not None:
            for attr in attrs:
                text = fmt_str % (ATTRIBUTES[attr], text)

        text += RESET
    return text


def get_logger(logger_name=u'deploy'):
    logger = logging.getLogger(logger_name.upper())
    logger.setLevel(logging.INFO)

    stream_formatter = logging.Formatter('%(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_formatter)

    logger.addHandler(stream_handler)

    return logger


def cmdline_parse():
    usage = u"usage: %prog [-D] dir1 dir2 dir3"
    parser = OptionParser(usage=usage)
    # parser.add_option(u"-O", u"--optimize", dest=u"optimize", action=u'store_true', default=False,
    #                   help=u"using -OO flags when compile python source")
    parser.add_option(u"-D", u"--delete-source", dest=u"delete_source", action=u'store_true', default=False,
                      help=u"delete python source file after compile it")
    parser.add_option(u"-d", u"--default-projects", dest=u"default_projects", action=u'store_true', default=False,
                      help=u"use default projects: ['/opt/scanner/src/scanner/', '/opt/proj/src/proj/', '/opt/pocs/src/pocs/']")
    options, args = parser.parse_args()
    if options.default_projects:
        args = ['/opt/scanner/src/scanner/']
    if not args:
        parser.error('You must provide directories that you want to compile')
    return options, args


def main():
    global options
    options, args = cmdline_parse()
    directories = args
    m = defaultdict(lambda: defaultdict(lambda: 0))
    for directory in directories:
        if os.path.isdir(directory):
            for r, ds, fs in os.walk(directory):
                for f in fs:
                    if not f.endswith('.py'):
                        continue
                    py = os.path.join(r, f)
                    if '__init__.py' in py or py.endswith('main.py'):
                        continue
                    #pyc = '%sc' % py
                    pyo = '%so' % py
                    #if os.path.exists(pyc) and os.path.isfile(pyc):
                    #    os.remove(pyc)
                    if os.path.exists(pyo) and os.path.isfile(pyo):
                        os.remove(pyo)
                    print 'Compile %s to %s ... ' % (py, 'pyo'),
                    code, output = commands.getstatusoutput(
                        'python -m py_compile %s && python -OO -m py_compile %s' % (py, py))
                    if code == 0:
                        print colored('Success', 'green')
                        if ENCRYPT:
                            if os.path.isfile(py+'c'):
                                encrypt_file(py+'c')
                            if os.path.isfile(py+'o'):
                                encrypt_file(py+'o')
                        m[directory]['success'] += 1
                        if options.delete_source:
                            if py in IGNORE_FILES:
                                continue
                            #if py.endswith('__init__.py'):
                            #    continue
                            commands.getstatusoutput('rm -f %s' % py)
                    else:
                        print colored('Failed: %s' % output.strip())
                        m[directory]['fail'] += 1
        else:
            logger.info(colored('Directory %s does not exist' % directory, 'red'))
    for directory in m:
        if 'success' in m[directory]:
            print 'Total %s files compile success under %s' % (
            colored(str(m[directory]['success']), 'green'), directory)
        if 'fail' in m[directory]:
            print 'Total %s files compile failed under %s' % (colored(str(m[directory]['fail']), 'green'), directory)


if __name__ == u'__main__':
    logger = get_logger()
    main()
