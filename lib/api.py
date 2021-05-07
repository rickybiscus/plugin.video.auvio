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

# SimplePlugin
from simpleplugin.simpleplugin import Plugin
from simpleplugin.simpleplugin import Addon

# Plugin modules
from . import common
from . import utils

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

def get_single_channel(cid,url_params={}):

    #return a single channel

    url_params['id'] = cid #set/override channel ID in URL params
    channels = get_channel_list(url_params)

    if not channels:
        return

    filtered = [ch for ch in channels if ch['id']==cid]

    if not filtered:
        return

    #return first one
    return filtered[0]


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
def get_media_details(mid,live=False):
    # Get the media details by a ID from the API

    common.plugin.log('get_media_details')

    if live:
        url = common.cryo_base_url + 'live/planningdetail'
    else:
        url = common.cryo_base_url + 'media/objectdetail'

    url_params = {
        'partner_key':  common.cryo_partner_key,
        'v':            8,
        'target_site':  'mediaz',
        'id':           mid
    }

    common.plugin.log("api.get_media_details media #{0} - is live:{1}".format(mid,live))

    try:
        json_data = utils.request_url(url,url_params)
        if not json_data:
            return

        data = json.loads(json_data)

    except:
        common.plugin.log_error("api.get_media_details - failed for media #{0}".format(mid))
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


#Get the encoded authorisation XML for medias that have a DRM
def get_drm_media_auth(user_token,mid,is_live=False):

        #Return base64 encoded KeyOS authentication XML (Widevine)

        #https://www.buydrm.com/multikey-demo
        #https://bitmovin.com/mpeg-dash-hls-drm-test-player/
        #http://dashif.org/reference/players/javascript/v2.4.1/samples/dash-if-reference-player/index.html

        url = common.cryo_base_url + 'drm/encauthxml'
        url_params = {
            'partner_key':  common.cryo_partner_key,
            'v':            8,
        }

        #live ?
        if is_live:
            url_params['planning_id'] = mid
        else:
            url_params['media_id'] = mid

        url_headers = {
            'Authorization':    "Bearer " + user_token,
        }

        json_data = utils.request_url(url,url_params,url_headers)

        if json_data:

            data = json.loads(json_data)
            auth = data.get('auth_encoded_xml')

            common.plugin.log("media #{0} auth: {1}".format(mid,auth))

            return auth


        return None
