#!/usr/bin/python
# -*- coding: utf-8 -*-

# Module: main
# Author: G.Breant
# Created on: 04.10.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
import re
import math

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

# Plugin modules
import common
import scraper
import api
import utils

medias_per_page = 20


# initialize_gettext
#_ = common.plugin.initialize_gettext()



def popup(text, time=5000, image=None):
    title = common.plugin.addon.getAddonInfo('name')
    icon = common.plugin.addon.getAddonInfo('icon')
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, text,time, icon))
      
@common.plugin.action()
def root(params):
    
    listing = []
    
    listing.append({
        'label':    'TV en direct',
        'url':      common.plugin.get_url(action='list_videos_live')
    })  # Item label
    
    listing.append({
        'label':    'Radio en direct',
        'url':      common.plugin.get_url(action='list_radios_live')
    })  # Item label
    
    listing.append({
        'label':    'Chaînes',
        'url':      common.plugin.get_url(action='list_channels')
    })  # Item label

    listing.append({
        'label':    'Émissions',
        'url':      common.plugin.get_url(action='list_shows')
    })  # Item label
    
    listing.append({
        'label':    'Catégories',
        'url':      common.plugin.get_url(action='list_categories')
    })  # Item label


    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = None, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )


@common.plugin.action()
def menu_single_channel(params):
    
    channel_id = params.get('id')
    
    listing = []

    listing.append({
        'label':    'Récent',
        'url':      common.plugin.get_url(action='list_medias',filter_medias='channel_medias_recent',id=channel_id)
    })  # Item label

    listing.append({
        'label':    'Sélection',
        'url':      common.plugin.get_url(action='list_medias',filter_medias='channel_medias_selection',id=channel_id)
    })  # Item label

    listing.append({
        'label':    'Émissions',
        'url':      common.plugin.get_url(action='list_medias',filter_medias='channel_medias_shows',id=channel_id)
    })  # Item label


    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = None, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )

@common.plugin.action()
@common.plugin.cached(common.cachetime_categories)
def list_categories(params):
    
    listing = []
    
    categories = api.get_media_categories()

    for item in categories:
        li = api.category_to_kodi_item(item)
        listing.append(li)  # Item label
        
    sortable_by = {
        xbmcplugin.SORT_METHOD_LABEL
    }

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )

@common.plugin.action()
@common.plugin.cached(common.cachetime_channels)
def list_channels(params):
    
    listing = []
    
    channels = api.get_channels()

    for channel in channels:
        li = api.channel_to_kodi_item(channel)
        listing.append(li)  # Item label

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = None, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )


@common.plugin.action()
@common.plugin.cached(common.cachetime_live)
def list_videos_live(params):
    listing = []
    response = scraper.get_live_videos()
    if response:
        listing = get_medias_list(response,params)
    
    sortable_by = {
        xbmcplugin.SORT_METHOD_DATE
    }

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )

@common.plugin.action()
@common.plugin.cached(common.cachetime_live)
def list_radios_live(params):
    response = scraper.get_live_radios()
    if response:
        listing = get_medias_list(response,params)

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )

@common.plugin.action()
def list_medias(params):
    
    common.plugin.log("list_medias")
    common.plugin.log(json.dumps(params))
    
    filter_medias =    params.get('filter_medias',None)
    page = int(params.get('page',1))
    id = params.get('id',None)
    response = None
    listing = []

    #show
    if filter_medias == 'medias_single_show':
        response = api.get_recent_medias_for_show(id)
        medias = response.get('medias')
    #channel
    elif filter_medias == 'channel_medias_live':
        medias = scraper.get_channel_medias(id,'live')
    elif filter_medias == 'channel_medias_recent':
        medias = scraper.get_channel_medias(id,'recent')
    elif filter_medias == 'channel_medias_selection':
        medias = scraper.get_channel_medias(id,'selection')
    elif filter_medias == 'channel_medias_shows':
        medias = scraper.get_channel_medias(id,'shows')
    elif filter_medias == 'category_medias':
        id = params.get('id')
        medias = scraper.get_category_medias(id)

    if medias:
        listing = get_medias_list(medias,params)
    
    sortable_by = {
        xbmcplugin.SORT_METHOD_DATE,
        xbmcplugin.SORT_METHOD_DURATION
    }

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )


@common.plugin.action()
@common.plugin.cached(common.cachetime_shows)
def list_shows(params):
    
    listing = []
    shows = api.get_shows()
    
    for item in shows:        
        li = api.show_to_kodi_item(item)
        listing.append(li)

    return common.plugin.create_listing(
        listing,
        #succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )

def get_medias_list(items,params):
    listing = []
    
    common.plugin.log("get_medias_list")
    common.plugin.log(json.dumps(params))

    for item in items:
        li = api.media_to_kodi_item(item)
        listing.append(li)  # Item label
        
        
    page =  int(params.get('page',1))

    pagination_params = {
        'page':     page,
        'total':    len(listing),
        'action':   params.get('action',None),
        'id':       params.get('id',None)
    }

    #menu link
    link_root = navigate_root()
    listing.append(link_root)
    
    #pagination link
    link_next = navigate_next(pagination_params)
    if link_next:
        listing.append(link_next)
  
    return listing
    

@common.plugin.action()
def stream_live(params):
    lid = params.get('live_id');
    common.plugin.log("STREAM LIVE#" + str(lid))
    url = api.get_live_video_url(lid)

    if not url:
        popup("media file not found")
        common.plugin.log_error("media file not found")
        return

    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

@common.plugin.action()
def stream_radio(params):
    radio_slug = params.get('radio_slug')
    radio_config = api.get_live_radio_config(radio_slug)
    streams = radio_config.get('flashAudioUrls')
    common.plugin.log('streams')
    common.plugin.log(streams)
    stream = streams[0] #get first one (TO FIX better way to choose it ?)
    url = stream.get('url')

    if not url:
        popup("media file not found")
        common.plugin.log_error("media file not found")
        return
    
    common.plugin.log("stream radio url: %s" % url)
    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
            
@common.plugin.action()
def stream_media(params):
    
    media_id = params.get('media_id')
    media_type = params.get('media_type')
    data = api.get_media_details(media_id,media_type)
    
    common.plugin.log("stream_media() type:%s, id:#%s" % (media_type,media_id))
    common.plugin.log(json.dumps(data))

   
    if 'downloadUrl' in data:
        url = data.get('downloadUrl','')
    elif 'highUrl' in data:
        url = data.get('highUrl','')
    elif 'url' in data:
        url = data.get('url','')
    else:
        url = ''
            
    if not url:
        popup("media file not found")
        common.plugin.log_error("media file not found")
        return
        
    common.plugin.log("stream media url: %s" % url)
    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
    
def navigate_next(params):
    
    page =      int(params.get('page',1)) + 1
    total =     params.get('total',1)
    action =    params.get('action',None)
    id =        params.get('id',None)
    pages = math.floor(total/medias_per_page)

    if total <= (page * medias_per_page):
        return

    title = "Next page (%d/%d)" % (page,pages)

    link = {
        'label':    title,
        'url':      common.plugin.get_url(
                        action=         action,
                        id=             id,
                        page=           page
                    )
    }
    
    return link

def navigate_root():
    return {
        'label':    "Back to menu",
        'url':      common.plugin.get_url(action='root')
    }


# Start plugin from within Kodi.
if __name__ == "__main__":
    # Map actions
    # Note that we map callable objects without brackets ()
    common.plugin.run()
    

def get_live_urlOLD(lid):
    common.plugin.log("get_live_rtmp for ID#" + lid)
    
    url = scraper.get_live_url(lid)
    data = utils.request_url(url)

    regex = r"""streamName&quot;:&quot;([^&]+)"""
    stream_name = re.search(regex, data)
    if stream_name is None:
        return None
    stream_name = stream_name.group(1)
    common.plugin.log("stream name: >" + stream_name + "<")
    if stream_name == 'freecaster':
        common.plugin.log("freecaster stream")
        regex = r"""streamUrl&quot;:&quot;([^&]+)"""
        freecaster_stream =  re.search(regex, data)
        freecaster_stream = freecaster_stream.group(1)
        freecaster_stream=freecaster_stream.replace("\\", "") 
        return freecaster_stream
    else:
        common.plugin.log("not a freecaster stream")
        regex = r"""streamUrlHls&quot;:&quot;([^&]+)"""
        hls_stream_url = re.search(regex,data)
        if hls_stream_url is not None:
            common.plugin.log("HLS stream")
            stream_url = hls_stream_url.group(1).replace("\\", "")
            data = channel.get_url(stream_url)
            best_resolution_path = data.split("\n")[-2]
            hls_stream_url = stream_url[:stream_url.rfind('open')] + best_resolution_path[5:]
            common.plugin.log("HLS stream url: >" + hls_stream_url + "<")
            return hls_stream_url
        else:
            regex = r"""streamUrl&quot;:&quot;([^&]+)"""
            stream_url = re.search(regex,data)
            if stream_url is not None:
                stream_url = stream_url.group(1)
                stream_url = stream_url.replace("\\", "")
                common.plugin.log("strange stream:" +stream_url)
                return stream_url
            else:
                common.plugin.log("normal stream")
                token_url = api.rtbf_url_api + 'media/streaming?streamname=%s' % stream_name
                token_json_data = utils.request_url(token_url,url)
                token = token_json_data.split('":"')[1].split('"')[0]
                swf_url = 'http://static.infomaniak.ch/livetv/playerMain-v4.2.41.swf?sVersion=4%2E2%2E41&sDescription=&bLd=0&sTitle=&autostart=1'
                rtmp = 'rtmp://rtmp.rtbf.be/livecast'
                page_url = 'http://www.rtbf.be'
                #page_url = api.rtbf_url ?
                play = '%s?%s' % (stream_name, token)
                rtmp += '/%s swfUrl=%s pageUrl=%s tcUrl=%s' % (play, swf_url, page_url, rtmp)
                return rtmp

    
