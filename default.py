# -*- coding: utf-8 -*-
import sys
import os
import json
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from xml.dom import minidom

# Script constants
__addon__ = xbmcaddon.Addon()
__cwd__ = xbmcvfs.translatePath(__addon__.getAddonInfo('path'))

# Shared resources
BASE_RESOURCE_PATH = os.path.join(__cwd__, 'resources', 'lib')
sys.path.append(BASE_RESOURCE_PATH)


def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
                and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s" % (newl))
        for node in self.childNodes:
            if node.nodeType is not minidom.Node.TEXT_NODE:
                node.writexml(writer, indent+addindent, addindent, newl)
        writer.write("%s</%s>%s" % (indent, self.tagName, newl))
    else:
        writer.write("/>%s" % (newl))


# replace minidom's function with ours
minidom.Element.writexml = fixed_writexml


def get_kodi_version():
    query = {
        "jsonrpc": "2.0",
        "method": "Application.GetProperties",
        "params": {
            "properties": ["version", "name"]
        },
        "id": 1
    }
    json_query = xbmc.executeJSONRPC(json.dumps(query))
    json_query = json.loads(str(json_query))
    if 'result' in json_query and 'version' in json_query['result'] and 'major' in json_query['result']['version']:
        return json_query['result']['version']['major']


def change_font_size():
    addonspath = os.path.dirname(os.path.dirname(__cwd__))
    filepath = os.path.join(addonspath, 'script.cu.lrclyrics', 'resources',
                            'skins', 'Default', '1080i', 'script-cu-lrclyrics-main.xml')
    if not os.path.exists(filepath):
        xbmcgui.Dialog().notification('LyricsFontSize', '未找到指定文件',
                                      xbmcgui.NOTIFICATION_INFO, 2000, False)
        return

    doc = minidom.parse(filepath)
    root = doc.documentElement

    nodes = root.getElementsByTagName('control')
    lyrics_node = None
    title_node = None
    for i in range(len(nodes)):
        if nodes[i].getAttribute('id') == '110':
            lyrics_node = nodes[i]
            title_node = nodes[i-1]
            break

    if not lyrics_node:
        xbmcgui.Dialog().notification('LyricsFontSize', '修改失败，未找到对应结点',
                                      xbmcgui.NOTIFICATION_INFO, 2000, False)
        return

    current_title_font_size = title_node.getElementsByTagName("font")[0].firstChild.data.strip()
    current_lyrics_font_size = lyrics_node.getElementsByTagName("font")[0].firstChild.data.strip()

    title_font_size_list = ['font20_title', 'font25_title', 'font30_title',
                            'font32_title', 'font36_title', 'font40_title', 'font45_title', 'font52_title']
    kodi_version = get_kodi_version()
    if kodi_version and kodi_version == 19:
        lyrics_font_size_list = ['font10', 'font12', 'font13',
                                'font14', 'font27', 'font37', 'font45', 'font60']
    else:
        lyrics_font_size_list = ['font10', 'font12', 'font13',
                                'font14', 'font27', 'font32', 'font37', 'font45', 'font60']

    sel0 = xbmcgui.Dialog().select('请选择要改变字体大小的项目', ['标题字体大小', '歌词字体大小'])
    if sel0 < 0:
        return
    elif sel0 == 0:
        font_size_list = title_font_size_list
        show_list = [e+' (当前字体大小)' if e == current_title_font_size else e for e in title_font_size_list]
    else:
        font_size_list = lyrics_font_size_list
        show_list = [e+' (当前字体大小)' if e == current_lyrics_font_size else e for e in lyrics_font_size_list]

    sel = xbmcgui.Dialog().select('请选择字体大小', show_list)

    if sel < 0:
        return
    else:
        font_size = font_size_list[sel]

    if sel0 == 0:
        node = title_node.getElementsByTagName('font')[0]
        newText = doc.createTextNode(font_size)
        node.replaceChild(newText, node.firstChild)
    elif sel0 == 1:
        for node in lyrics_node.getElementsByTagName("font"):
            newText = doc.createTextNode(font_size)
            node.replaceChild(newText, node.firstChild)
    with open(filepath, 'w', encoding='utf-8') as f:
        doc.writexml(f, addindent="    ", newl="\n")

    if sel0 == 0:
        info = '标题字体大小已替换成: ' + font_size
    else:
        info = '歌词字体大小已替换成: ' + font_size

    xbmcgui.Dialog().notification('LyricsFontSize', info,
                                  xbmcgui.NOTIFICATION_INFO, 2000, False)


change_font_size()
