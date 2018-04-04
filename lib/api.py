#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
API methods (RTBF/Auvio)
"""

# API data
channels = None

import os
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
import urllib

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

from simpleplugin import Addon
import common
import utils

@common.plugin.cached(common.cachetime_app_settings) 
def get_app_settings():
    #Get app settings (menu items & some other variables)
    
    url = common.cryo_base_url + 'setting/settinglist'
    url_params = {
        'partner_key':  common.cryo_partner_key,
        'v':            7
    }

    json_data = utils.request_url(url,url_params)
    datas = json.loads(json_data)
    common.plugin.log("api.get_app_settings")
    common.plugin.log(json_data)
    return datas

def get_menu_categories():
    app_datas = get_app_settings()
    categories = app_datas['settings']['menu']['categories']
    return categories

def get_menu_channels():
    app_datas = get_app_settings()
    categories = app_datas['settings']['menu']['channels']
    return categories

@common.plugin.cached(common.cachetime_app_settings)
def get_channel_list(url_params={}):
    #Get ALL the channels from the API (not only the menu ones), including radios.  Can be filtered through optionnal url parameters.
    
    #url params
    url_params_default = {
        'partner_key':  common.cryo_partner_key,
        'v':            7,
    }
    
    url_params = utils.parse_dict_args(url_params_default,url_params)

    common.plugin.log("api.get_channel_list")

    url = common.cryo_base_url + 'epg/channellist'

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return

    data = json.loads(json_data)

    return data

@common.plugin.cached(common.cachetime_medias_recent)
def get_sidebar_widget_list(sidebar_id):

    url_params = {
        'sidebar_id':   sidebar_id,
        'partner_key':  common.cryo_partner_key,
        'v':            7,
    }

    common.plugin.log("api.get_sidebar_widget_list: #" + str(sidebar_id))

    url = common.cryo_base_url + 'widget/widgetlist'

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return

    data = json.loads(json_data)
    common.plugin.log(json_data)

    return data

@common.plugin.cached(common.cachetime_medias_recent)
def get_widget_detail(widget_id):
    url_params = {
        'id':   widget_id,
        'partner_key':  common.cryo_partner_key,
        'v':            8,
    }

    common.plugin.log("api.get_widget_detail: #" + str(widget_id))

    url = common.cryo_base_url + 'widget/widgetdetail'

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return

    data = json.loads(json_data)
    #common.plugin.log(json_data)

    return data

@common.plugin.cached(common.cachetime_media_data)
def get_media_details(id):
    """
    Get the media details by a ID from the API.  If the type is None, we'll try to query both methods.
    """
    
    common.plugin.log('get_media_details')

    url = common.cryo_base_url + 'media/objectdetail'
    url_params = {
        'partner_key':  common.cryo_partner_key,
        'v':            7,
        'target_site':  'mediaz',
        'id':           id,
    }

    common.plugin.log("get_media_details for ID:%s" % (id))

    try:
        json_data = utils.request_url(url,url_params)
        if not json_data:
            return
 
        data = json.loads(json_data)

    except:

        common.plugin.log_error('Unable to get media details for %s #%s' % (id))
        return None

    common.plugin.log(json.dumps(data))
    return data

def get_live_videos(page=1):
    # parse live video streams

    items = []
    
    limit = int(Addon().get_setting('medias_per_page'))

    url = common.cryo_base_url + 'live/planninglist'
    url_params = {
        'target_site':  'mediaz',
        #'offset':       (page - 1) * limit,
        #'limit':        limit,
        'partner_key':  common.cryo_partner_key,
        'v':            8,
    }
    
    #API request
    json_data = None
    json_data = utils.request_url(url,url_params)

    #handle datas
    if not json_data:
        return
    else:
        nodes = json.loads(json_data)
        common.plugin.log('api.get_live_videos: found %d nodes' % len(nodes))
        return nodes

def get_user_favorites(user_token, type='media', offset = None,limit = None):
    
    nodes = []
    
    if user_token:
    
        #TOFIX what if not / bad token ?

        url = common.cryo_base_url + 'media/favorite/favoritelist'
        url_params = {
            'type':         type,
            'partner_key':  common.cryo_partner_key,
            'v':            8,
            'include_drm':  'true',
        }

        if offset:
            url_params['offset'] = offset

        if limit:
            url_params['limit'] = limit

        url_headers = {
            'Accept':           "application/json",
            'Authorization':    "Bearer " + user_token,
        }

        json_data = utils.request_url(url,url_params,url_headers)

        if json_data:
            nodes = json.loads(json_data)

    common.plugin.log('api.get_user_favorites: found %d nodes' % len(nodes))
    
    return nodes