#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103,C0111

from __future__ import print_function
import shutil
from lxml import html
import requests
from make_epub import make_epub

BASE_URL = 'http://www.liaoxuefeng.com'

def main():
    mkdir_p('./wiki/images')

    r = requests.get(raw_input('Input URL:'))
    if r.status_code != 200:
        return

    h = html.fromstring(r.text)
    ul = h.cssselect('.x-sidebar-left-content ul[style]')[0]

    chapter = {}
    menu = []

    #f = open('./wiki/index.md', 'wb')
    for li in ul:
        depth = 0
        try:
            style = li.attrib['style']
            depth = int(style[12])
        except KeyError:
            pass

        a = li[0]
        url = a.attrib['href']
        title = a.text
        if isinstance(title, unicode):
            title = title.encode('utf-8')

        chapter_text = get_chapter_text(chapter, depth)

        save_html(url, title, chapter_text)

        print('%s %s %s' % (chapter_text, title.decode('utf-8'), url))
        #f.write('%s. [%s](%s.html)\n' % (chapter_text, title, chapter_text))
        menu.append((depth, title, chapter_text))

    #f.close()

    #import cPickle as pickle
    #pickle.dump(menu, open('./menu.dat', 'wb'))
    make_epub(menu)

def mkdir_p(path):
    import os
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def save_html(url, title, chapter_text):
    r = requests.get(BASE_URL + url)
    if r.status_code != 200:
        return False

    h = html.fromstring(r.text)
    contentdiv = h.cssselect('.x-wiki-content')[0]

    # Remove broken videos
    for div in contentdiv.cssselect('div[data-type=video]'):
        div.getparent().remove(div)

    save_imgs(contentdiv)

    with open('./wiki/%s.html' % chapter_text, 'wb') as f:
        head = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{0}</title><script src="highlight.js"></script><script>hljs.initHighlightingOnLoad();</script><link rel="stylesheet" href="highlight.css"></head>
<body><h1>{0}</h1>
<hr>'''
        f.write(head.format(title))
        f.write((''.join(html.tostring(e, encoding='utf-8') for e in contentdiv)).strip())
        f.write('</body>\n</html>')

def save_imgs(contentdiv):
    for img in contentdiv.cssselect('img[alt]'):
        src = img.attrib['src']
        alt = img.attrib['alt']
        try:
            alt = alt.encode('ascii')
        except UnicodeEncodeError:
            alt = alt.encode('utf-8').encode('hex_codec').upper()

        r = requests.get(BASE_URL + src, stream=True)
        if r.status_code != 200:
            break

        file_type = r.headers['content-type'].split('/', 2)[1]
        if file_type == 'jpeg':
            file_type = 'jpg'

        with open('./wiki/images/%s.%s' % (alt, file_type), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        img.attrib['src'] = 'images/%s.%s' % (alt, file_type)

def get_chapter_text(chapter, depth):
    if depth == 0:
        chapter_text = '0'
    else:
        try:
            chapter[depth - 1] += 1
        except KeyError:
            chapter[depth - 1] = 1
        chapter[depth] = 0
        chapter_text = '.'.join([str(chapter[i]) for i in range(depth)])
    return chapter_text

if __name__ == '__main__':
    main()
