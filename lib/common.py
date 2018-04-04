#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
Stuff shared between the python files
"""

import os
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

# SimplePlugin
from simpleplugin import Plugin
from simpleplugin import Addon

# Create plugin instance
plugin = Plugin()

rtbf_url = 'http://www.rtbf.be/'
cryo_base_url = rtbf_url + "api/partner/generic/"
cryo_partner_key = '97a0ceb4562f285ba770aaba6c81d047'
auvio_url = 'http://www.rtbf.be/auvio/'

#in minutes
cachetime_app_settings = 60 * 24
cachetime_channels = 60 * 24
cachetime_programs = 60 * 24
cachetime_media_data = 60 * 24
cachetime_medias_recent = 15

def popup(text, time=5000, image=None):
    title = plugin.addon.getAddonInfo('name')
    icon = plugin.addon.getAddonInfo('icon')
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, text,time, icon))
    
def ask(question):
    dialog = xbmcgui.Dialog()
    title = plugin.addon.getAddonInfo('name')
    return dialog.yesno(title, question)
