#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
API methods (RTBF/Auvio)
"""

# API data
main_data = None
channels = None
categories = None

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


def get_base_datas():
    """
    Fetch the header nav datas from API and clean it (menu items)
    """
    
    global main_data
    if main_data is None:

        url = common.rtbf_url + 'news/api/menu'
        url_params = {
            'site':  'media', # 'data-site' attr from body
        }
        
        progressdialog = xbmcgui.DialogProgress()
        progressdialog.create(common.plugin.addon.getAddonInfo('name'))
        progressdialog.update(0, 'Récupération des données...')
        
        common.plugin.log("get_base_datas")
        
        try:
            
            json_data = utils.request_url(url,url_params)
            if not json_data:
                return
            
            main_data = json.loads(json_data) #will generate unicode
            main_data = clean_base_datas(main_data)
            progressdialog.update(100, 'Done!')
            
        except:
            main_data = False
            progressdialog.update(0, 'Échec!')
            xbmc.sleep(1000)
        
        progressdialog.close()
        
    #common.plugin.log("before clean_base_datas:")
    #common.plugin.log(json.dumps(main_data))

    #common.plugin.log("after clean_base_datas:")
    #common.plugin.log(json.dumps(main_data))
    
    return main_data

def clean_base_datas(node):
    """
    Recursive function that does cleanup the main JSON from get_base_datas() so it's easier to handle
    """
    new_node = {}
    new_node_id = None
    for key in node:
        node_data = node[key]
        if key == '@attributes':
            for attr in node_data:
                value = node_data[attr]
                if attr == 'id':
                    new_node_id = value
                else:
                    new_node[attr] = value
            
        else:
            new_item = {}
            for item in node_data:
                item_dict = clean_base_datas(item)
                item_id = item_dict.get('id')
                new_item[item_id] = item_dict.get('value')
                
            new_node['items'] = new_item
            
    if new_node_id:
        return {
            'id':       new_node_id,
            'value':    new_node
        }
    else:
        return new_node


@common.plugin.cached(common.cachetime_categories)
def get_categories():
    """
    Extract the categories fetched in get_base_datas()
    """

    global categories
    
    if not categories :

        common.plugin.log("api.get_categories")

        base_datas = get_base_datas()
        items = base_datas.get('items').get('category').get('items')
        categories = []
        
        for category_slug in items:
            
            category_raw = items.get(category_slug)
            category = {}

            try:
                prefix, id = category_slug.split('category-')
                category['id'] = id
            except:
                common.plugin.log_error("api.get_channels(): skipping category '%s'" % category_slug)
                pass

            if category.get('id'):
                category['name'] = category_raw['name'].encode('utf-8').strip()
                categories.append(category)

    return categories

@common.plugin.cached(common.cachetime_channels)
def get_channels():
    """
    Get channels from the API
    """
    
    global channels
    
    if not channels :

        common.plugin.log("api.get_channels")

        items = []

        url = common.cryo_base_url + 'epg/channellist'
        url_params = {
            'partner_key':  common.rtbf_api_key,
            'v':            7,
        }
    
        json_data = utils.request_url(url,url_params)
        if not json_data:
            return
        
        channels = json.loads(json_data)

    return channels

def get_single_channel_by_id(id = None):
    
    if not id: 
        common.plugin.log_error('api.get_single_channel_by_id() : parameter id is missing')
        return None

    common.plugin.log("get_single_channel by ID:"+str(id))

    for channel in get_channels():
        if id == channel.get('id',0):
            return channel
    
@common.plugin.cached(common.cachetime_media_data)
def get_media_details(id):
    """
    Get the media details by a ID from the API.  If the type is None, we'll try to query both methods.
    """
    
    common.plugin.log('get_media_details')

    url = common.cryo_base_url + 'media/objectdetail'
    url_params = {
        'partner_key':  common.rtbf_api_key,
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


def get_live_radio_config(radio_slug):
    
    """
    Get radio informations from the API
    """
    
    #get config.json
    config_url = 'http://www.rtbf.be/radio/liveradio/rtbf/radios/%s/config.json' % radio_slug
    json_data = utils.request_url(config_url)
    if not json_data:
        return
    
    common.plugin.log('config.json')
    common.plugin.log(json_data)
    data = json.loads(json_data)
    
    return data


def get_live_videos(page=1):
    """
    parse live video streams
    """
    items = []
    
    limit = int(Addon().get_setting('medias_per_page'))

    url = common.cryo_base_url + 'live/planninglist'
    url_params = {
        'partner_key':  common.rtbf_api_key,
        'v':            7,
        'target_site':  'media',
        'origin_site':  'media',
        'category_id':  0,
        'start_date':   '',
        'offset':       (page - 1) * limit,
        'limit':        limit,
    }

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return
    
    nodes = json.loads(json_data)

    common.plugin.log('api.get_live_videos: found %d nodes' % len(nodes))

    return nodes

def get_channel_current_live(channel_slug):

    items = []
    
    url = common.cryo_base_url + 'live/planningcurrent'
    url_params = {
        'partner_key':  common.rtbf_api_key,
        'v':            7,
        'target_site':  'mediaz',
        'channel':      channel_slug
    }

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return
    
    node = json.loads(json_data)

    return node

def get_category_medias(id,page=1):

    items = []
    
    limit = int(Addon().get_setting('medias_per_page'))

    url = common.cryo_base_url + 'media/objectlist'
    url_params = {
        'partner_key':  common.rtbf_api_key,
        'v':            7,
        'target_site':  'mediaz',
        'category_id':  id,
        'offset':       (page - 1) * limit,
        'limit':        limit,
    }

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return
    
    nodes = json.loads(json_data)

    common.plugin.log('api.get_category_medias: found %d nodes' % len(nodes))
    
    return nodes

def get_program_medias(id,page=1):
    """
    Get a list of recent medias by show ID or IDs, from the API
    """

    items = []
    
    limit = int(Addon().get_setting('medias_per_page'))
    
    url = common.cryo_base_url + 'media/objectlist'
    url_params = {
        'partner_key':  common.rtbf_api_key,
        'v':            7,
        'program_id':   id,
        'target_site':  'mediaz',
        'offset':       (page - 1) * limit,
        'limit':        limit,
    }

    json_data = utils.request_url(url,url_params)
    if not json_data:
        return
    
    nodes = json.loads(json_data)

    common.plugin.log('api.get_program_medias: found %d nodes' % len(nodes))
    
    return nodes

def get_user_favorites(user_token, type='media', offset = None,limit = None):
    
    nodes = []
    
    if user_token:
    
        #TOFIX what if not / bad token ?

        url = common.cryo_base_url + 'media/favorite/favoritelist'
        url_params = {
            'type':         type,
            'partner_key':  common.rtbf_api_key,
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