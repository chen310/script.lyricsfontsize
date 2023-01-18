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
addonspath = os.path.dirname(os.path.dirname(__cwd__))

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


def getres(addon_path):
    filepath = os.path.join(addon_path, 'addon.xml')
    doc = minidom.parse(filepath)
    root = doc.documentElement
    items = root.getElementsByTagName('extension')
    for item in items:
        point = item.getAttribute('point')
        if point == 'xbmc.gui.skin':
            ress = item.getElementsByTagName('res')
            list = []
            for res in ress:
                if res.getAttribute('folder') not in list:
                    list.append(res.getAttribute('folder'))
            return list
    return []


def get_fonts(filepath):
    doc = minidom.parse(filepath)
    root = doc.documentElement
    fontsets = root.getElementsByTagName('fontset')
    if fontsets:
        font_node = fontsets[0]
    else:
        return

    title_font_size_list = []
    lyrics_font_size_list = []

    for node in font_node.getElementsByTagName("name"):
        font = node.firstChild.data.strip()
        if font.startswith("font"):
            if font.endswith("_title"):
                title_font_size_list.append(font)
            elif font[4:].isdigit():
                lyrics_font_size_list.append(font)
    return title_font_size_list, lyrics_font_size_list


def change_font_size():
    skin_path = xbmcvfs.translatePath('special://skin')
    res_path = getres(skin_path)
    if res_path:
        res_path = res_path[0]
        font_xml_path = os.path.join(skin_path, res_path, 'Font.xml')
    else:
        font_xml_path = ''
    if os.path.exists(font_xml_path):
        title_font_size_list, lyrics_font_size_list = get_fonts(font_xml_path)
    else:
        title_font_size_list = ['font20_title', 'font25_title', 'font30_title',
                                'font32_title', 'font36_title', 'font40_title', 'font45_title', 'font52_title']
        kodi_version = get_kodi_version()
        if kodi_version and kodi_version == 19:
            lyrics_font_size_list = ['font10', 'font12', 'font13',
                                     'font14', 'font27', 'font37', 'font45', 'font60']
        else:
            lyrics_font_size_list = ['font10', 'font12', 'font13',
                                     'font14', 'font27', 'font32', 'font37', 'font45', 'font60']

    lyrics_xml_path = os.path.join(
        skin_path, res_path, 'script-cu-lrclyrics-main.xml')
    if os.path.exists(lyrics_xml_path):
        filepath = lyrics_xml_path
        has_custom_lyrics_file = True
    else:
        filepath = os.path.join(addonspath, 'script.cu.lrclyrics', 'resources',
                                'skins', 'Default', '1080i', 'script-cu-lrclyrics-main.xml')
        has_custom_lyrics_file = False

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

    labels = title_node.getElementsByTagName("label")
    if labels and "MusicPlayer.Title" in labels[0].firstChild.data:
        has_title = True
    else:
        has_title = False

    if has_title:
        current_title_font_size = title_node.getElementsByTagName("font")[0].firstChild.data.strip()
    current_lyrics_font_size = lyrics_node.getElementsByTagName("font")[0].firstChild.data.strip()

    if has_title:
        menus = ['标题字体大小', '歌词字体大小']
    else:
        menus = ['歌词字体大小']
    if has_custom_lyrics_file:
        sel0 = xbmcgui.Dialog().select('请选择要改变字体大小的项目('  + os.path.basename(os.path.dirname(skin_path)) + ')', menus)
    else:
        sel0 = xbmcgui.Dialog().select('请选择要改变字体大小的项目', menus)
    if sel0 < 0:
        return
    elif sel0 == 0 and has_title:
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

    if sel0 == 0 and has_title:
        node = title_node.getElementsByTagName('font')[0]
        newText = doc.createTextNode(font_size)
        node.replaceChild(newText, node.firstChild)
    else:
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
