#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import pinyin
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
-n, --dry-run     don't actually add fileds, just show how it works.
-h, --help        show this messge.
-f, --force       add fileds no matter whether the info exist.
'''

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

def deal_with_mp3(file_name, quiet, overwrite, dryrun):
    try:
        tag = eyeD3.tag.Mp3AudioFile(file_name).getTag()
    except:
        return False

    # print tag
    if tag:
        modified = False
        print_str = ''
        for fd in FIDS:
            text = fd[1](tag)
            # print text
            if (overwrite or not tag.frames[fd[0]]) \
                    and text and contain_cjk_char(text):
                value = pinyin.hanzi2pinyin(text)
                try:
                    tag.setTextFrame(fd[0], value)
                    modified = True
                    print_str += "\t%s: %s (%s)\n" % (fd[2], value,
    text)
                    # print print_str
                except FrameException, ex:
                    pass

        if modified:
            tag_version = tag.getVersion()
            if tag_version == ID3_V2_4:
                tag.setTextEncoding(UTF_8_ENCODING)
                # keep the ID3 v2.4 version
                update_version = ID3_CURRENT_VERSION
            else:
                update_version = ID3_V2_4
                # v1.x supports ISO-8895 only
                if tag_version & ID3_V1:
                    tag.setTextEncoding(LATIN1_ENCODING)
                else:
                    # UTF-8 is not supported by v2.3
                    tag.setTextEncoding(UTF_16_ENCODING)
            try:
                if not (dryrun or tag.update(update_version)):
                    return False
            except:
                return False
            if not quiet:
                print file_name
                print print_str.encode(sys_encoding)
            return True
    return False

def main(argv=None):
    opt_recursive = False
    opt_quiet = False
    opt_overwrite = False
    opt_dryrun = False
    suc = 0
    if argv is None: argv = sys.argv
    try:
        try:
            opts, args = \
                getopt.getopt(argv[1:], \
                    "hnrqf", ["help", "recursive", "quiet", "dry-run"])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-r", "--recursive"):
                opt_recursive = True
            if option in ("-q", "--quiet"):
                opt_quiet = True
            if option in ("-f", "--force"):
                opt_overwrite = True
            if option in ("-n", "--dry-run"):
                opt_dryrun = True

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    for f in args:
        if os.path.isfile(f):
            if deal_with_mp3(f, opt_quiet, opt_overwrite, opt_dryrun):
                suc = suc + 1
        elif os.path.isdir(f):
            if opt_recursive:
                for root, dirs, fileNames in os.walk(f):
                    # ignore hidden dirs and files
                    dirs = [d for d in dirs if d[0]!='.']
                    files = [f for f in fileNames if f[0]!='.']
                    for ff in files:
                        ff = os.path.join(root, ff)
                        if deal_with_mp3(ff, opt_quiet, opt_overwrite, opt_dryrun):
                            suc = suc + 1
            else:
                for ff in os.listdir(f):
                    ff = os.path.join(f, ff)
                    if os.path.isfile(ff):
                        if deal_with_mp3(ff, opt_quiet, opt_overwrite, opt_dryrun):
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
    if opt_dryrun:
        print >> sys.stderr, "It seems to work well"
    return 0

if __name__ == "__main__":
    sys.exit(main())
