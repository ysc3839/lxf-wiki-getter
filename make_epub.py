#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103,C0111,E1101

from __future__ import print_function
import sys
import os
import mimetypes
from zipfile import ZipFile, ZIP_DEFLATED
from uuid import uuid4
from lxml import etree

uuid = str(uuid4())

def make_epub(menu):
    gen_ncx(menu)
    gen_metadata(menu)
    make_zip()

def make_zip():
    cwd = os.path.dirname(os.path.abspath(sys.argv[0]))

    epub_file = 'lxf-wiki.epub'
    if os.path.exists(epub_file):
        os.remove(epub_file)

    zf = ZipFile(epub_file, 'w', ZIP_DEFLATED)
    for folder in ['./wiki/']:
        os.chdir(os.path.join(cwd, folder))
        add_folder(zf, '.', None)
    zf.close()

def add_folder(zf, folder, count):
    children = os.listdir(folder)
    children.sort()
    for name in children:
        name = os.path.join(folder, name)
        if os.path.isdir(name):
            count = add_folder(zf, name, count)
        else:
            zf.write(name)
            if count is not None:
                count += 1
                if (count % 10) == 0:  # optimize
                    sys.stdout.write(str(count)+'\r')
                    sys.stdout.flush()

    return count

def gen_ncx(menu):
    ncx = etree.Element('ncx', {'xmlns': 'http://www.daisy.org/z3986/2005/ncx/', 'version': '2005-1'}) # , 'xml:lang': 'zh-CN'
    head = etree.SubElement(ncx, 'head')

    etree.SubElement(head, 'meta', {'name': 'dtb:uid', 'content': uuid})
    etree.SubElement(head, 'meta', {'name': 'dtb:depth', 'content': str(len(menu))})
    etree.SubElement(head, 'meta', {'name': 'dtb:generator', 'content': 'lxf-wiki-getter'})
    etree.SubElement(head, 'meta', {'name': 'dtb:totalPageCount', 'content': '0'})
    etree.SubElement(head, 'meta', {'name': 'dtb:maxPageNumber', 'content': '0'})

    elementWithText(ncx, 'docTitle', menu[0][1])

    navMap = etree.SubElement(ncx, 'navMap')
    navPointCount = 1
    rootnp = etree.SubElement(navMap, 'navPoint', {'id': 'num_%d' % navPointCount, 'playOrder': str(navPointCount)})

    elementWithText(rootnp, 'navLabel', menu[0][1])
    etree.SubElement(rootnp, 'content', {'src': '%s.html' % menu[0][2]})

    lastnp = rootnp

    last_depth = 0
    for item in menu:
        depth, title, chapter_text = item
        navPointCount += 1
        if depth == 0:
            navPointCount -= 1
        else:
            i = 1 - (depth - last_depth)
            for _ in range(i):
                lastnp = lastnp.getparent()
            lastnp = etree.SubElement(lastnp, 'navPoint', {'id': 'num_%d' % navPointCount, 'playOrder': str(navPointCount)})
            elementWithText(lastnp, 'navLabel', title)
            etree.SubElement(lastnp, 'content', {'src': '%s.html' % chapter_text})
        last_depth = depth

    with open('./wiki/ncx.ncx', 'wb') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(etree.tostring(ncx, encoding='utf-8', pretty_print=True))

def gen_metadata(menu):
    with open('./wiki/metadata.opf', 'wb') as f:
        f.writelines('<?xml version="1.0"  encoding="utf-8"?>')
        f.writelines('<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id">')
        f.writelines('<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">')
        f.writelines('<dc:title>%s</dc:title>' % menu[0][1])
        f.writelines('<dc:identifier opf:scheme="uuid" id="uuid_id">%s</dc:identifier>' % uuid)
        f.writelines('<dc:creator opf:role="aut">廖雪峰</dc:creator>')
        f.write('<dc:language>zh</dc:language>\n</metadata>\n<manifest>\n')
        f.writelines('<item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>')
        f.writelines('<item href="highlight.css" id="hlcss" media-type="text/css"/>')

        itemrefs = []
        for item in menu:
            _id = item[2].replace('.', '-')
            itemrefs.append('h-%s' % _id)
            f.writelines('<item href="%s.html" id="h-%s" media-type="application/xhtml+xml"/>' % (item[2], _id))

        for imgname in os.listdir('./wiki/images/'):
            f.writelines('<item href="images/%s" id="img-%s" media-type="%s"/>' % (imgname, imgname.split('.', 2)[0], mimetypes.guess_type(imgname)))

        f.write('</manifest>\n<spine toc="ncx">\n')

        for ref in itemrefs:
            f.writelines('<itemref idref="%s"/>' % ref)

        f.write('</spine>\n<guide/>\n</package>\n')

def elementWithText(parent, tag, text):
    element = etree.SubElement(parent, tag)
    etree.SubElement(element, 'text').text = text.decode('utf-8')

if __name__ == '__main__':
    import cPickle as pickle
    menu = pickle.load(open('./menu.dat', 'rb'))
    make_epub(menu)
