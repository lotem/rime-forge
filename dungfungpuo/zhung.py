#! /usr/bin/env python
# this script performs middle chinese to mandarin conversion
# according to user selected options
# it is once a web service hosted on google appengine

'''
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
'''

import logging
import os
import re
import StringIO
import sys
import urllib

dir = os.path.dirname(sys.argv[0])
file_name = os.path.join(dir, 'zhung.txt')

# provide a comma separated list of options as command line argument
# prefix an option with ! to deselect it
default_options = 'gi-j,!zi-j,!v-w,bu,zhi,zr-zh,!zr-z,!rh-r,!zh-z,!l-n,' \
                  'ueng-ung,ien-ian,uon-uan,m-n,!ng-n,rhy-el,o-eo,ptk-h,' \
                  '!5-tones,4-tones,!2-tones,!1-tone'

rules = {
    'gi-j' : [
        (r'^gi', r'ji'),
        (r'^ki', r'qi'),
        (r'^hi', r'xi'),
        (r'^([jqx])i([aoeu])', r'\1\2'),
    ],
    'zi-j' : [
        (r'^zi', r'ji'),
        (r'^ci', r'qi'),
        (r'^si', r'xi'),
        (r'^([jqx])i([aoeu])', r'\1\2'),
    ],
    'v-w' : [
        (r'^v([aoeu])', r'w\1'),
        (r'^vi', r'wui'),
    ],
    'bu' : [
        (r'^([bpmfv])un(\w*)$', r'\1en\2'),
        (r'^([bpm])uon(\d?)$', r'\1an\2'),
        #(r'^([bpm])u([ae]\w*)$', r'\1\2'),
    ],
    'zhi' : [
        (r'^([zcsr]h)i(\d?)$', r'\1y\2'),
        (r'^([zcsr]h)i([mn]\w*)$', r'\1e\2'),
        (r'^([zcsr]h)i(u?)e([mn]\d?)$', r'\1\2a\3'),
        (r'^([zcsr]h)i(u?)e([ptkh]?\d?)$', r'\1\2o\3'),
        (r'^([zcsr]h)io([ptkh]?\d?)$', r'\1uo\2'),
        (r'^([zcsr]h)i([aoeu]\w*)$', r'\1\2'),
        #(r'^([zcs])ri(\d?)$', r'\1hy\2'),
        #(r'^([zcs]r)i([mn]\w*)$', r'\1e\2'),
        #(r'^([zcs]r)i(u?)e([mn]\d?)$', r'\1\2a\3'),
        (r'^([zcs]r)i(u?)e([ptkh]?\d?)$', r'\1\2o\3'),
        #(r'^([zcs]r)io([ptkh]?\d?)$', r'\1uo\2'),
        #(r'^([zcs]r)i([aoeu]\w*)$', r'\1\2'),
    ],
    'zr-zh' : [
        (r'^([zcs])r', r'\1h'),
    ],
    'zr-z' : [
        (r'^([zcs])r', r'\1'),
    ],
    'rh-r' : [
        (r'^rh([aei])', r'r\1'),
        (r'^rhou', r'rou'),
    ],
    'zh-z' : [
        (r'^([zcsr])h', r'\1'),
        (r'^([zcs])r', r'\1'),
    ],
    'l-n' : [
        (r'^l', r'n'),
    ],
    'ueng-ung' : [
        #(r'weng(\d?)$', r'wung\1'),
        (r'ueng(\d?)$', r'ung\1'),
        (r'([yi])uek(\d?)$', r'\1uk\2'),
    ],
    'ien-ian' : [
        (r'([jqxyi]u?)e([mn]\d?)$', r'\1a\2'),
    ],
    'uon-uan' : [
        (r'([wu])o(n\d?)$', r'\1a\2'),
    ],
    'm-n' : [
        (r'm(\d?)$', r'n\1'),
    ],
    'ng-n' : [
        (r'ng(\d?)$', r'n\1'),
    ],
    'rhy-el' : [
        (r'^rh?y(\d?)$', r'el\1'),
    ],
    'o-eo' : [
        (r'(^|[^jqxyiwu])o([ptkh]?\d?)$', r'\1eo\2'),
    ],
    'ptk-h' : [
        (r'[ptk](\d?)$', r'h\1'),
    ],
    '5-tones' : [
        (r'([ptkh])2$', r'\1'),
    ],
    '4-tones' : [
        (r'[ptkh]2$', r'2'),
        (r'[ptkh]$', r'1'),
    ],
    '2-tones' : [
        (r'\d$', r''),
    ],
    '1-tone' : [
        (r'\d$', r''),
        (r'[ptkh]$', r''),
    ],
}

def compile_rules():
    for r in rules:
        try:
            rules[r] = [(re.compile(p[0]), p[1]) for p in rules[r]]
        except:
            logging.error('error compiling rule %s.' % r)

compile_rules()

def apply_rules(s, selected_rules):
    return reduce(lambda s, p: p[0].sub(p[1], s), selected_rules, s)

def parse_table(f):
    g = lambda a: (a[-1], a[1])
    return [g(line.rstrip('\n').split('\t')) for line in f.readlines()]

table = []

def load_data():
    global table
    f = open(file_name)
    if not f:
        logging.error('error opening %s.' % file_name)
    try:
        table = parse_table(f)
    except:
        logging.error('error parsing %s.' % file_name)
        return
    logging.info('loaded %s.' % file_name)

load_data()

'''
class OptionsHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(default_options)

class ExportHandler(webapp.RequestHandler):
    def get(self, options=default_options):
        options = urllib.unquote(options)
        result = memcache.get(options)
        if result is None:
            # start a new transformation task
            selected_rules = [x for k in options.split(',') if k in rules for x in rules[k]]
            out = StringIO.StringIO()
            print >> out, '# generated with options: %s' % options
            if not memcache.add(options, [False, 0, selected_rules, set(), out], 60):
                logger.error('memcache set failed.')
            taskqueue.add(url='/zhung/transform', params={'options': options})
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers['Refresh'] = '5'
            self.response.out.write('your request is being processed, please re-visit this URL later for the results.')
            return
        if not result[0]:
            # report transformation progress
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers['Refresh'] = '5'
            self.response.out.write('transformation in progress: %d/%d.' % (result[1], len(table)))
            return
        # transformation finished, proceed export
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.headers['Content-Disposition'] = 'attachment; filename = zhung-keywords.txt'
        self.response.out.write(result[-1].getvalue())

class TransformHandler(webapp.RequestHandler):
    batch_limit = 1000
    def get(self):
        self._process()
    def post(self):
        self._process()
    def _process(self):
        options = self.request.get('options')
        result = memcache.get(options)
        if not result or result[0]:
            return
        (finished, start, selected_rules, keywords, out) = result
        if start == len(table):
            result[0] = True
            print >> out, '# distinct keywords: %d' % len(keywords)
            for s in sorted(keywords):
                print >> out, '# %s' % s
            memcache.set(options, result)
            return
        try:
            for s, z in table[start:start + TransformHandler.batch_limit]:
                s = apply_rules(s, selected_rules)
                if s not in keywords:
                    keywords.add(s)
                print >> out, '\t'.join([s, z])
                result[1] += 1
        except DeadlineExceededError:
            TransformHandler.batch_limit = (result[1] - start) / 3 + 1
            Logger.warn('deadline exceeded, transformation batch limit reset to %d.' % TransformHandler.batch_limit)
        memcache.set(options, result, 60)
        taskqueue.add(url='/zhung/transform', params={'options': options})

application = webapp.WSGIApplication([(r'/zhung/options', OptionsHandler),
                                      (r'/zhung/export/default', ExportHandler),
                                      (r'/zhung/export/(.*)', ExportHandler),
                                      (r'/zhung/transform', TransformHandler),
                                     ],
                                     debug=True)
'''

def main():
    #run_wsgi_app(application)

    options = sys.argv[1] if len(sys.argv) > 1 else default_options
    print '#', options

    selected_rules = [x for k in options.split(',') if k in rules for x in rules[k]]
    for s, z in table:
        s = apply_rules(s, selected_rules)
        #if s not in keywords:
        #    keywords.add(s)
        print '\t'.join([z, s])

if __name__ == '__main__':
    main()
