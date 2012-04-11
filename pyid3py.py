#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import glob
from pinyin import PINYIN_DICT
from eyeD3.tag import Mp3AudioFile, \
    FrameException, \
    InvalidAudioFormatException

HELP_MESSAGE = '''
pyid3py.py [OPTION] TARGET

Convert Chinese characters in mp3 ID3 to PinYin.

-r, --recursive   act on directory recursively.
-p, --preferred   don't prompt. prefer default pronunciation
                  for Hanzi with multi-pronunciation
-f, --force       add fileds no matter whether the info exist.
-n, --dry-run     don't actually add fileds, just show how it works.
-h, --help        show this messge.
'''


def is_cjk_char(x):
    x = ord(x)
    # Punct & Radicals
    if x >= 0x2e80 and x <= 0x33ff:
        return True
    # Fullwidth Latin Characters
    if x >= 0xff00 and x <= 0xffef:
        return True
    # CJK Unified Ideographs &
    # CJK Unified Ideographs Extension A
    if x >= 0x4e00 and x <= 0x9fbb:
        return True
    # CJK Compatibility Ideographs
    if x >= 0xf900 and x <= 0xfad9:
        return True
    # CJK Unified Ideographs Extension B
    if x >= 0x20000 and x <= 0x2a6d6:
        return True
    # CJK Compatibility Supplement
    if x >= 0x2f8000 and x <= 0x2fa1d:
        return True
    return False


def contain_cjk_char(text):
    for char in text:
        if is_cjk_char(char):
            return True
    return False


def hanzi2pinyin(text):
    """

    Convert Chinese characters in `text' to pinyin.
    `text' should be unicode string.

    """
    pinyin_seq = []
    for char in text:
        if char in PINYIN_DICT:
            pinyin = PINYIN_DICT[char]
            if isinstance(pinyin, basestring):
                pinyin_seq.append(pinyin)
            elif len(pinyin) == 1:
                pinyin_seq.append(pinyin[0])
            else:
                pinyin_seq.append(pinyin)
        else:
            pinyin_seq += (char,)
    return pinyin_seq


def prompt(text, cookies={}):
    """

    Prompt when multi-pronunciation Chinese characters in `text' occur.

    """
    if text in cookies:
        return cookies[text]
    pinyin = ''
    for i, candidates in enumerate(hanzi2pinyin(text)):
        if isinstance(candidates, basestring):
            pinyin += candidates
        elif isinstance(candidates, (tuple, list, set)):
            while True:
                ps = '  >> %s[%s]%s { %s } ' % \
                     (text[0:i], text[i:i + 1], text[i + 1:],
                      '  '.join('%d.%s' % (j + 1, c)
                                for j, c in enumerate(candidates)))
                try:
                    choice = int(raw_input(ps.encode('utf-8'))) - 1
                except ValueError:
                    continue
                except EOFError:
                    print
                    continue
                if choice in range(len(candidates)):
                    pinyin += candidates[choice]
                    break
    cookies[text] = pinyin
    return pinyin


def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hnrfp",
                                   ["help", "recursive",
                                    "dry-run", 'force',
                                    'preferred'])
    except getopt.error as err:
        print >> sys.stderr, os.path.basename(sys.argv[0]) + \
            ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        sys.exit(1)
    opts = [k for k,v in opts]
    contains = lambda x, y: x in opts or y in opts
    if contains('-h', '--help'):
        print HELP_MESSAGE
        sys.exit(0)
    recursive = contains("-r", "--recursive")
    force = contains("-f", "--force")
    dryrun = contains("-n", "--dry-run")
    preferred = contains('-p', '--preferred')
    cookies = {}
    processed = []

    def handle(file):
        print file
        try:
            tag = Mp3AudioFile(file).getTag()
        except InvalidAudioFormatException as err:
            print >>sys.stderr, '  %s: %s' % \
                (os.path.basename(file), err.message)
            return
        modified = False
        for text, sort_frame, title in ((tag.getArtist(), 'TSOP', "Artist:"),
                                        (tag.getAlbum(),  'TSOA', "Album :"),
                                        (tag.getTitle(),  'TSOT', "Name  :")):
            print ' ', title, text
            if (force or not tag.frames[sort_frame]) and \
               text and contain_cjk_char(text):
                if preferred:
                    pinyin = ''.join(c[0] if isinstance(c, tuple) else c
                                     for c in hanzi2pinyin(text))
                else:
                    pinyin = prompt(text, cookies)
                    try:
                        tag.setTextFrame(sort_frame, pinyin)
                        modified = True
                    except FrameException as err:
                        print >> sys.stderr, err.message
        if modified:
            processed.append(file)
            if not dryrun:
                tag.update()
        print

    def batch(pathes):
        [handle(path) for path in pathes
         if os.path.isfile(path) and path.lower().endswith('.mp3')]

    for path in reduce(lambda x, y: x + y, map(glob.glob, args)):
        try:
            if os.path.isfile(path):
                handle(path)
            elif os.path.isdir(path):
                if recursive:
                    for root, dirs, files in os.walk(path):
                        batch([os.path.join(root, f) for f in files])
                else:
                    batch([os.path.join(path, f) for f in os.listdir(path)])
            else:
                print >> sys.stderr, "File Not Found: %s" % path
                sys.exit(2)
        except KeyboardInterrupt:
            print
            break
    success = len(processed)
    if success == 0:
        print >> sys.stderr, "No file processed."
    elif success == 1:
        print >> sys.stderr, "1 file processed."
    elif success > 1:
        print >> sys.stderr, "%d files processed." % success
    if dryrun:
        print >> sys.stderr, "It seems to work well"
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
