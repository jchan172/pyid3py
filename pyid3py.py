#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
from pinyin import PinYinDict
from eyeD3.tag import *;

FIDS = [("TSOP", Tag.getArtist, "Sort Artist"),
        ("TSOA", Tag.getAlbum , "Sort Album"),
        ("TSOT", Tag.getTitle , "Sort Name")]

sys_encoding = sys.getfilesystemencoding()
help_message = '''
pyid3py.py [OPTION] TARGET

Convert Chinese characters in ID3 to PinYin,
and also *update* the ID3 tag version to v2.4.

-r, --recursive   act on directory recursively.
-q, --quiet       print nothing except the result.
-p, --preferred   don't prompt. prefer default pronunciation for Hanzi with multi-pronunciation
-f, --force       add fileds no matter whether the info exist.
-n, --dry-run     don't actually add fileds, just show how it works.
-h, --help        show this messge.
'''

_cookies = {}
_options = {}

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def is_cjk_char(x):
    # Punct & Radicals
    if x >= 0x2e80 and x <= 0x33ff:
        return 1

    # Fullwidth Latin Characters
    if x >= 0xff00 and x <= 0xffef:
        return 1

    # CJK Unified Ideographs &
    # CJK Unified Ideographs Extension A
    if x >= 0x4e00 and x <= 0x9fbb:
        return 1
    # CJK Compatibility Ideographs
    if x >= 0xf900 and x <= 0xfad9:
        return 1

    # CJK Unified Ideographs Extension B
    if x >= 0x20000 and x <= 0x2a6d6:
        return 1

    # CJK Compatibility Supplement
    if x >= 0x2f8000 and x <= 0x2fa1d:
        return 1

    return 0

def contain_cjk_char(line):
    # print "@: %s" % (line.encode("utf-8"))
    for ch in line:
        if is_cjk_char(ord(ch)):
            return 1
    return 0

def hanzi2pinyins(hanzi):
    """ hanzi should be unicode string"""
    pinyin = ()
    for char in hanzi:
        char_ord = ord(char)
        if char_ord in PinYinDict:
            if len(PinYinDict[char_ord])==1:
                pinyin += (PinYinDict[char_ord][0],)
            else:
                pinyin += (PinYinDict[char_ord],)
        else:
            pinyin += (char,)
    return pinyin

def prompt(text, candidates):
    if text in _cookies:
        return _cookies[text]
    result = ''
    for i, c in enumerate(candidates):
        if type(c) is str:
            result +=c
        elif type(c) is tuple:
            while True:
                # te[x]t
                print text[0:i] + '[' + text[i:i+1] + ']' + text[i+1:] + ': ',
                for j, e in enumerate(c):
                    print "(%d) %s  " % (j+1, e),
                print
                choosed = sys.stdin.readline().strip()
                try:
                    if int(choosed) not in range(1, len(c)+1):
                        raise ValueError
                    result += c[int(choosed)-1]
                    break
                except ValueError:
                    continue
    _cookies[text] = result
    return result

def deal_with_mp3(file_name):
    global _options
    try:
        tag = eyeD3.tag.Mp3AudioFile(file_name).getTag()
    except:
        return False
    if tag:
        modified = False
        print_str = ''
        for fd in FIDS:
            text = fd[1](tag).strip()
            if (_options['force'] or not tag.frames[fd[0]]) \
                    and text and contain_cjk_char(text):
                # if "-p" in options or "--prompt":
                if _options['preferred']:
                    value = ''.join([i[0] if type(i) is tuple else i
                                     for i in hanzi2pinyins(text)])
                else:
                    value = prompt(text, hanzi2pinyins(text))
                try:
                    tag.setTextFrame(fd[0], value)
                    modified = True
                    print_str += "\t%s: %s (%s)\n" % (fd[2], value, text)
                except FrameException, ex:
                    pass

        if modified:
            tag_version = tag.getVersion()
            if tag_version == eyeD3.ID3_V2_4:
                tag.setTextEncoding(UTF_8_ENCODING)
                # keep the ID3 v2.4 version
                update_version = eyeD3.ID3_CURRENT_VERSION
            else:
                update_version = eyeD3.ID3_V2_4
                # v1.x supports ISO-8895 only
                if tag_version & eyeD3.ID3_V1:
                    tag.setTextEncoding(LATIN1_ENCODING)
                else:
                    # UTF-8 is not supported by v2.3

                    # NOTE
                    # Setting encoding to utf-16be or utf-16
                    # will cause the arkwork lose!

                    # tag.setTextEncoding(UTF_16BE_ENCODING)
                    # tag.setTextEncoding(UTF_16_ENCODING)
                    pass
            try:
                if not (_options['dryrun'] or tag.update(update_version)):
                    return False
            except:
                return False
            if not _options['quiet']:
                print file_name
                print print_str.encode(sys_encoding)
            return True
    return False

def main(argv=None):
    global _options
    suc = 0
    if argv is None: argv = sys.argv
    try:
        try:
            opts, args = \
                getopt.getopt(argv[1:], \
                    "hnrqfp", ["help", "recursive", "quiet", "dry-run", 'force', 'preferred'])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        opt_func = lambda x, y: ((x, '') in opts) or ((y, '') in opts)
        if opt_func('-h', '--help'):
            raise Usage(help_message)
        _options['recursive'] = opt_func("-r", "--recursive")
        _options['quiet'] = opt_func("-q", "--quiet")
        _options['force'] = opt_func("-f", "--force")
        _options['dryrun'] = opt_func("-n", "--dry-run")
        _options['preferred'] = opt_func('-p', '--preferred')
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    for f in args:
        if os.path.isfile(f):
            if deal_with_mp3(f):
                suc = suc + 1
        elif os.path.isdir(f):
            if _options['recursive']:
                for root, dirs, fileNames in os.walk(f):
                    # ignore hidden dirs and files
                    dirs = [d for d in dirs if d[0]!='.']
                    files = [f for f in fileNames if f[0]!='.']
                    for ff in files:
                        ff = os.path.join(root, ff)
                        if deal_with_mp3(ff):
                            suc = suc + 1
            else:
                for ff in os.listdir(f):
                    ff = os.path.join(f, ff)
                    if os.path.isfile(ff):
                        if deal_with_mp3(ff):
                            suc = suc + 1
        else:
            print >> sys.stderr, "File Not Found: %s" % f
            return 2

    if suc==0:
        print >> sys.stderr, "No file processed."
    elif suc==1:
        print >> sys.stderr, "1 file processed."
    elif suc>1:
        print >> sys.stderr, "%d files processed." % suc

    if _options['dryrun']:
        print >> sys.stderr, "It seems to work well"
    return 0

if __name__ == "__main__":
    sys.exit(main())
