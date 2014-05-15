Introduction
============

This is a script to replace ID3 tags containing Chinese characters with PinYin because some car systems or audio players cannot display Chinese characters. Specifically, the title, artist, and album tags are the ones that will be replaced. Note that the script doesn't work with ID3v2.2 because eyeD3 doesn't support ID3v2.2. If using iTunes, ensure that mp3s are converted to ID3v2.3 or ID3v2.4 (IDv2.3 tested working) by selecting all the songs, right-clicking, and selecting 'Convert ID3 Tags...'.

###Example:

If a song's ID3 title was '想你的夜', it would get converted to 'XiangNiDeYe'


Requirements
============

    pip install eyeD3

Tested working with Python 2.7.5.

Usage
======

    python pyid3py.py [OPTION] TARGET

    Convert Chinese characters in mp3 ID3 title, artist, and album tags to PinYin.

    -r, --recursive   act on directory recursively.
    -p, --preferred   don't prompt. prefer default pronunciation
                      for Hanzi with multi-pronunciation.
    -f, --force       add fileds no matter whether the info exist.
    -n, --dry-run     don't actually add fileds, just show how it works.
    -h, --help        show this messge.

Note that the -f option must be used in order to replace the original Chinese characters with PinYin, so the typical usage would be:

    python pyid3py.py -f ~/Music/想你的夜.mp3

or to go recursively through a directory:

    python pyid3py.py -f -r ~/Music/

Modifications
=============

The script may be modified to replace other tags, instead of title, artist, and album. Please refer to the ID3v2.3 or ID3v2.4 specification. The `id3_frame` may be changed in lines 149-151 in `pyid3py.py`. 

**Use at your own risk.**
