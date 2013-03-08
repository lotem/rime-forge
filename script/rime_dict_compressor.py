#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fileinput
import os
import sys

vocabulary_file = "essay.txt"

vocabulary = {}
if os.path.exists(vocabulary_file):
  for line in open(vocabulary_file):
    t = line.rstrip().split("\t")
    if len(t) < 2: continue
    vocabulary[t[0]] = int(t[1])

word_list = []
word_table = {}
phrase_list = []
phrase_table = {}

file_header = []
table_has_begun = False
reading_yaml = False

for line in fileinput.input():
  line = line.rstrip()
  if not table_has_begun:
    if reading_yaml:
      if line == '...':
        reading_yaml = False
      print line
      continue
    elif line == '---':
      reading_yaml = True
      print line
      continue
    elif not line or line.startswith('#'):
      print line
      continue
    else:
      table_has_begun = True
      pass
  t = line.split("\t")
  if not t: continue
  text = t[0]
  if len(t) < 2 and text not in phrase_table:
    if text not in phrase_table:
      phrase_list.append(text)
    phrase_table[text] = []
    continue
  code = t[1]
  freq_str = ''
  freq = 0
  if text in vocabulary:
    freq = vocabulary[text]
  if len(t) >= 3:
    freq_str = t[2]
    if freq_str[-1] == '%':
      freq = freq * float(freq_str[:-1]) / 100.0
    else:
      freq = int(freq_str)
  value = (freq, code, freq_str)
  if len(code.split(' ')) == 1:
    if text not in word_table:
      word_list.append(text)
    if text in word_table:
      row = word_table[text]
      row.append(value)
    else:
      row = word_table[text] = [value]
  else:
    if text not in phrase_table:
      phrase_list.append(text)
    if text in phrase_table:
      row = phrase_table[text]
      row.append(value)
    else:
      row = phrase_table[text] = [value]

def output(text, row):
  for freq, code, freq_str in row:
    t = [text, code]
    if freq_str:
      t.append(freq_str)
    print "\t".join(t)

ratio = {}
polyphone = {}
for word in word_list:
  row = word_table[word]
  #print >> sys.stderr, 'word:', word, 'row:', row
  output(word, row)
  # 計算多音字各讀音使用頻次的比例
  total = sum([freq for freq, code, freq_str in row]) or 1
  r = [(float(freq) / total, code, freq_str) for freq, code, freq_str in row]
  freq_cmp = lambda x, y: -cmp(x[0], y[0]) or cmp (x[1], y[1])
  r.sort(cmp=freq_cmp)
  ratio[word] = r
  # 只把多音字的常用讀音挑出來，用於自動注音
  frequent_codes = filter(lambda x: x[0] >= 0.05, r)
  #print >> sys.stderr, 'frequent_codes:', frequent_codes
  # 少見的讀音不用於自動注音
  if len(frequent_codes) > 1:
    polyphone[word] = frequent_codes
  elif not frequent_codes and len(r) > 1:
    polyphone[word] = r

for word, r in ratio.iteritems():
  for x in r:
    t = [word, x[1]]
    if len(r) > 1:
      t.append('%g%%' % round(x[0] * 100.0, 2))
    print >> sys.stderr, "\t".join(t)

def deduce_code(phrase, codes):
  global ratio, polyphone
  #print >> sys.stderr, 'deduce_code:', phrase, codes
  if not phrase:
    return codes
  result = []
  for i in range(1, len(phrase) + 1):
    if phrase[:i] in word_table:
      word = phrase[:i]
      remaining = phrase[i:]
      #print >> sys.stderr, 'len:', i, '[%s]' % word, '[%s]' % remaining
      if word in polyphone:
        ss = polyphone[word]
        #print >> sys.stderr, 'polyphone[%s]:' % word, ss
      elif word in ratio:
        ss = ratio[word][:1]
        #print >> sys.stderr, 'ratio[%s][:1]:' % word, ss
      else:
        print >> sys.stderr, 'surprise!', word
        continue
      result.extend(deduce_code(phrase[i:], [x + [s] for x in codes for f, s, f_str in ss]))
  return result

new_phrase_count = 0
for phrase in phrase_list:
  #print >> sys.stderr, 'phrase:', phrase
  row = phrase_table[phrase]
  # custom freq info given; take down
  custom_freq = any([bool(freq_str) for freq, code, freq_str in row])
  if custom_freq:
    output(phrase, row)
    continue
  possible_code = set([' '.join(c) for c in deduce_code(phrase, [[]])])
  #print >> sys.stderr, 'possible_code:', possible_code
  # given phrase only; take down
  if not row:
    #if possible_code:
    #  output(phrase, [(0, c, '') for c in possible_code])
    #else:
    print phrase
    continue
  # custom code specified; take down
  specified_code = set([code for freq, code, freq_str in row])
  #print >> sys.stderr, 'specified_code:', specified_code
  if specified_code != possible_code:
    output(phrase, row)
    continue
  # new phrase? take down the phrase itself
  if phrase not in vocabulary:
    new_phrase_count += 1
    if new_phrase_count < 100:
      print >> sys.stderr, 'new phrase:', phrase
    elif new_phrase_count == 100:
        print >> sys.stderr, 'new phrase: ...'
    print phrase
