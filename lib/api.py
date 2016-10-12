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

import common
import utils

def get_base_datas():
    """
    Fetch the header nav datas from API and clean it (menu items)
    """
    
    global main_data
    if main_data is None:
        
        site = 'media' # 'data-site' attr from body
        url = common.rtbf_url + 'news/api/menu?site=%s' % site 
        
        progressdialog = xbmcgui.DialogProgress()
        progressdialog.create(common.plugin.addon.getAddonInfo('name'))
        progressdialog.update(0, 'Fetching Data...')
        
        common.plugin.log("get_base_datas")
        
        try:
            json_data = utils.request_url(url)
            main_data = json.loads(json_data) #will generate unicode
            main_data = clean_base_datas(main_data)
            progressdialog.update(100, 'Done!')
        except:
            main_data = False
            progressdialog.update(0, 'Failed!')
            xbmc.sleep(1000)
        
        progressdialog.close()
        
    common.plugin.log("before clean_base_datas:")
    common.plugin.log(json.dumps(main_data))
        
    
    
    common.plugin.log("after clean_base_datas:")
    common.plugin.log(json.dumps(main_data))
    
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
def get_media_categories():
    """
    Extract the categories fetched in get_base_datas()
    """

    common.plugin.log("api.get_media_categories")

    base_datas = get_base_datas()
    items = base_datas.get('items').get('category').get('items')
    categories = []
    for cat_slug in items:
        category = items.get(cat_slug)
        try:
            prefix, id = cat_slug.split('category-')
            category['id'] = id
            categories.append(category)
        except:
            common.plugin.log("api.get_media_categories(): skipping category '%s'" % cat_slug)
            continue

    common.plugin.log(json.dumps(categories))
    
    return categories

@common.plugin.cached(common.cachetime_channels)
def get_channels():
    """
    Extract the channels fetched in get_base_datas()
    """
    
    global channels
    
    if not channels :

        common.plugin.log("api.get_channels")

        base_datas = get_base_datas()

        items = base_datas.get('items').get('channel').get('items')

        channels = []
        for channel_slug in items:
            channel = items.get(channel_slug)
            common.plugin.log(json.dumps(channel))

            try:
                prefix, id = channel_slug.split('channel-')
                channel['id'] = id
            except:
                common.plugin.log("api.get_channels(): skipping channel '%s'" % channel_slug)
                pass

            #append name to aliases so it easier to use get_single_channel_by_name()
            if channel.get('id'):
                aliases = []
                aliases.append(channel['name'])
                if 'aliases' in channel:
                    common.plugin.log(channel['aliases'])
                    aliases = aliases + channel['aliases'].split(',') 

                channel['aliases'] = aliases
                channels.append(channel)

    return channels

@common.plugin.cached(common.cachetime_channels)
def get_single_channel_by_name(name = None):
    
    if name:
        name = name.strip()
    
    if not name: 
        common.plugin.log_error('api.get_single_channel_by_name() : parameter name is missing')
        return None

    #TO FIX : cannot find channel with the name 'Ouftivi' for example

    for channel in get_channels():
        aliases = channel.get('aliases')
        if name in aliases:
            common.plugin.log(channel)
            return channel
          
@common.plugin.cached(common.cachetime_channels)
def get_single_channel_by_id(id = None):
    
    if not id: 
        common.plugin.log_error('api.get_single_channel_by_id() : parameter id is missing')
        return None

    common.plugin.log("get_single_channel by ID:"+id)
    for channel in get_channels():
        if channel.get('id') == id:
            common.plugin.log(channel)
            return channel
        
@common.plugin.cached(common.cachetime_shows)
def get_shows():
    
    """
    Get the list of shows from the API
    """
    
    common.plugin.log("api.get_shows()")

    shows = []
    retval = []
    
    #fetch datas
    try:
        url = common.auvio_url_api + 'emissions'
        json_data = utils.request_url(url)
        shows = json.loads(json_data)
    except:
        pass

    return shows

@common.plugin.cached(common.cachetime_shows)
def get_channel_shows(channel_id):
    
    """
    Filter the complete list of shows by channel ID
    """
    
    if not channel_id:
        common.plugin.log("api.get_channel_shows() : no input")
        return
    
    common.plugin.log("api.get_channel_shows()")
    
    retval = []
    shows = get_shows()
    
    for single_show in shows:
        show_channel_ids = []
        channels_names = single_show.get('channels')
        if channels_names and (len(channels_names) > 0):
            for channel_name in channels_names:
                channel = get_single_channel_by_name(channel_name)
                if channel.get('id',None):
                    show_channel_ids.append(channel.get('id'))
        
        #check for input channel ID
        if channel_id in show_channel_ids:
            retval.append(single_show)
        
    return retval




@common.plugin.cached(common.cachetime_medias_recent)
def get_recent_medias_for_show(ids,size=20,page=1):
    """
    Get a list of recent medias by show ID or IDs, from the API
    """

    medias = None
                             
    if not isinstance(ids, list):
        ids = [ids]

    #make IDs url parameter
    ids_str_arr = []
    id_k = 0
    for id in ids:
        ids_str_arr.append('ids[%d]=%s' % (id_k,id))
        id_k += 1
    
    ids_str = '&'.join(ids_str_arr)                   

    url = common.auvio_url_api + 'emissions-medias?%s&size=%s&page=%s' % (ids_str,size,page)  #see http://sgc.static.rtbf.be/js/tv/media/public/static/js/rtbf/myspace.js
    common.plugin.log('api.get_recent_medias_for_show() for show %s from url: %s' % (id,url))
    common.plugin.log(url)

    try:
        response_json = utils.request_url(url)
        response = json.loads(response_json) #will generate unicode
    except:
        pass

    if response:
        return response
    
@common.plugin.cached(common.cachetime_media_data)
def get_media_details(id,type):
    """
    Get the media details by a ID from the API.  If the type is None, we'll try to query both methods.
    """
    
    data = None

    if type is None:
        type = guess_media_type(id)

    url = None
    if type=='video':
         url = common.rtbf_url_api + 'media/video?method=getVideoDetail&args[]=%s' % id
    elif type=='audio':
         url = common.rtbf_url_api + 'media/audio?method=getAudioDetail&args[]=%s' % id

    common.plugin.log("get_media_details for ID:%s, type:%s - url = %s" % (id,type,url))

    try:

        json_data = utils.request_url(url)
        data = json.loads(json_data)
        data = data.get('data',None)

        common.plugin.log(json.dumps(data))

    except:

        common.plugin.log('Unable to get media details for %s #%s' % (type,id))
        return None

    return data

def guess_media_type(id):
    
    """
    If we don't know the media type, try to get info from 'video' or 'audio' to guess the type
    """
    
    #recursive; test both methods
    video_data = get_media_details(id,'video') #video
    if video_data:
        return 'video'
    
    audio_data = get_media_details(id,'audio') #audio
    if audio_data:
        return 'audio'


def channel_to_kodi_item(item):
    """
    Convert a channel API object to a kodi list item
    """
    
    
    li = {
            'label':    item.get('name'),
            'url':      common.plugin.get_url(action='menu_single_channel',id=item.get('id'))
        }
    return li

def category_to_kodi_item(item):
    
    """
    Convert a category API object to a kodi list item
    """
    
    li = {
        'label':    item.get('name'),
        'url':      common.plugin.get_url(action='list_medias',filter_medias='category_medias',id=item.get('id'))
    }
    return li

def show_to_kodi_item(item,show_channel=True):
    
    """
    Convert a show API object to a kodi list item
    """
    
    common.plugin.log('api.show_to_kodi_item()')
    common.plugin.log(item)
    
    #get image
    image = utils.get_srcset_image(item.get('imageSrcSet',None))
        
    #TO FIX use show.get('description')
    
    #label
    label_title = None
    label_channels = None
    
    if 'title' in item:
        label_title = item.get('title')
        
    if show_channel and ('channels' in item):
        label_channels = item.get('channels')
    
    label = utils.media_label(label_title,None,label_channels)
    
    li = {
        'label':    label,
        'url':      common.plugin.get_url(action='list_medias',filter_medias='medias_single_show',id=item.get('id')),
        'thumb':    image, # Item thumbnail
        'fanart':   image,
        'info': {
            'video': { ##http://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
                'plot':         item.get('description',''),#Long Description
                'plotoutline':  item.get('description',''),#Short Description
            }
        }

    }
    return li

def media_to_kodi_item(item, show_channel=True):
    """
    Format a media from the API to a kodi list item.
    Some values are defined with conditions, as the input sometimes differs 
    
    Based on 
    auvio> /api/emissions-medias 
    channel,date,date_w3c,description,duration,expire,expire_w3c,id,imageSrcSet,remainingDays, remainingHours,subtitle,title,type,url
    """
    
    common.plugin.log("api.media_to_kodi_item() for item #%s (type:%s)" % (item.get('id'),item.get('type')))
    common.plugin.log((json.dumps(item)))

    label = None
    date = None
    
    #image
    if item.get('thumbnail',None):
        image = 'http://ds1.static.rtbf.be' + item.get('thumbnail').get('medium')
    else:
        image = utils.get_srcset_image(item.get('imageSrcSet',None))

    #label
    label_title = None
    label_channels = None
    
    if 'name' in item:
        label_title = item.get('name')
    elif 'title' in item:
        label_title = item.get('title')
        
    if 'subtitle' in item:
        label_subtitle = item.get('subtitle')
        
    if show_channel and ('channel' in item):
        label_channels = item.get('channel')
    
    label = utils.media_label(label_title,label_subtitle,label_channels)
        

    #date
    if 'created' in item:
        date = utils.timestamp_to_kodi(item.get('created'))
    elif 'date_w3c' in item:
        date = utils.datetime_W3C_to_kodi(item.get('date_w3c')),
        
    #kodi type
    media_type = item.get('type')
    if media_type=='video' or media_type=='live':
        kodi_type = 'video'
    if media_type=='audio' or media_type=='radio':
        kodi_type = 'music'
        
    #url
    url = ''
    if media_type=='audio' or media_type=='video':
        url = common.plugin.get_url(action='stream_media',media_id=item.get('id'),media_type=item.get('type'))
    elif media_type=='live':
        url = common.plugin.get_url(action='stream_live',live_id=item.get('id'))
    elif media_type=='radio':
        url = common.plugin.get_url(action='stream_radio',radio_slug=item.get('channel'))
        
    #playable
    if url:
        is_playable = True
    else:
        is_playable = False

    li = {
        'label':    label,
        'thumb':    image, # Item thumbnail
        'fanart':   image,
        'url':      url,
        'info': {
            kodi_type: { ##http://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
                #'count':       item.get('songCount'),
                'plot':         item.get('description',''),#Long Description
                'plotoutline':  item.get('description',''),#Short Description
                'date':         date,
                #'aired':       date,
                'duration':     utils.convert_duration_str(item.get('duration')),
                #'artist':      item.get('artist'),
                #'album':       item.get('name'),
                #'year':        item.get('year')
            }
        },
        'is_playable':  is_playable
    }
    
    common.plugin.log(json.dumps(li))
    
    return li

@common.plugin.cached(common.cachetime_radio_config)
def get_live_radio_config(radio_slug):
    
    """
    Get radio informations from the API
    """
    
    #get config.json
    config_url = 'http://www.rtbf.be/radio/liveradio/rtbf/radios/%s/config.json' % radio_slug
    json_doc = utils.request_url(config_url)
    common.plugin.log('config.json')
    common.plugin.log(json_doc)
    data = json.loads(json_doc)
    
    return data

def get_live_video_url(lid):

    common.plugin.log('get_live_video_url for #' + lid)
    
    try:
        url =  common.rtbf_url + 'embed/d/ajax/refresh?id=%s' % lid
        json_response = utils.request_url(url)
        response = json.loads(json_response)
    
        common.plugin.log_error(json.dumps(response))
    
        data = response.get('data',{})
        stream = data.get('streamUrlHls',None)
    
        common.plugin.log_error(stream)
        return stream
        
    except:
        common.plugin.log_error('no stream URL found')
        return None



"""

def search(search,content = 'medias'):
    #content can be : 'programs','medias' 
    partner_id =    '82ed2c5b7df0a9334dfbda21eccd8427'
    url =           common.rtbf_url_api + 'search/media/autocomplete?partnerID=%s&content=%s&search%s' % (partner_id,content,search)
    data =          None

    common.plugin.log("search")

    try:
        json_data = utils.request_url(url)
        data = json.loads(json_data) #will generate unicode
    except:
        pass
    
    return data
    
def get_upcoming_medias_live(cat_id='',page=1,limit=10,fromTime=''):
    
    common.plugin.log('get_upcoming_medias_live')
    
    medias = []
        
    fromTime = utils.datetime_to_W3C() #TO FIX
    fromTime = '2016-10-09T23:26:12'

    #loaded on a live show page live
    url = common.auvio_url_api + 'live?page=%s&limit=%s&categoryId=%s&from=%s' % (page,limit,cat_id,fromTime)
    
    json_data = utils.request_url(url)
    medias = json.loads(json_data)

    common.plugin.log(url)
    common.plugin.log(json.dumps(medias))
    
    return medias
    
"""

"""

Some API endpoints : 

* news/api/menu?site=media - get website menu (categories, channels, ...) - see HTML body[data-site]
* auvio/api/emissions,{ids:r} - get list of shows
* auvio/api/emissions-medias?ids[0]=5&size=10&page=1&from=2016-10-07T00:39:03.719Z&excludes={} - get list of recent medias for shows, by IDs
* auvio/api/medias",{ids:i} ??? not sure for this one
* api/media/video?method=getVideoListByEmissionOrdered&args[]=5 - kind of same stuff ?
* api/media/video?method=getVideoDetail&args[]=2147753 - media details for a video
* api/media/audio?method=getAudioDetail&args[]=2146623 - media details for an audio
* api/time - get server time
* api/search/media/autocomplete?partnerID=82ed2c5b7df0a9334dfbda21eccd8427&content=medias&search=mini%20ninja - search results
* embed/m/api/timeline?id=2148163 - get streamling timeline for live media ?
* embed/m/api/suggest?id=2148163 - suggest videos for a media
* api/media/streaming?streamname=3D
* api/article/json?method=getChrono
* embed/d/ajax/refresh?id=70993 - refresh live informations

LIVE 

{"id":70993,"title":"JT 13h","type":"live","provider":"RTBFLIVE","programLabel":"Journal t\u00e9l\u00e9vis\u00e9 13h","programLabelKey":"journaltelevise13h","categoryLabel":"info-journaux","categoryLabelKey":"infojournaux","nopub":false,"thumbnail":"http://ds1.static.rtbf.be\/media\/program\/image\/ng_55a38eb6ea4db2f2d33a-original.png","geoLocRestriction":"open","sources":[],"streamName":"laune","streamUrlHls":"http:\/\/rtbf.l3.freecaster.net\/live\/rtbf\/geo\/open\/bc1e985c9592276a91bf1db4a6dd366efc9fc11e\/laune.m3u8?token=0db0ad0d41931810f148c","streamUrlDash":null,"startDate":"2016-10-12T12:53:00+02:00","endDate":"2016-10-12T13:42:00+02:00","isLive":true,"detailUrl":"http:\/\/www.rtbf.be\/auvio\/detail_journal-televise-13h?lid=70993"}" data-config="{"embedStaticVhost":"http://www.static.rtbf.be/rtbf/embed","wwwStaticVhost":"http://www.static.rtbf.be/rtbf/www","skin":"seven","suggestApiUrl":"http:\/\/www.rtbf.be\/embed\/m\/api\/suggest","videoApiUrl":"http:\/\/www.rtbf.be\/api\/media\/video","geoApiUrl":"http:\/\/www.rtbf.be\/api\/geoip","displayGeolocButton":false,"liveRefreshDataApiUrl":"http:\/\/www.rtbf.be\/embed\/d\/ajax\/refresh","prefetchUrl":"https:\/\/livevideo.infomaniak.com\/get_url.php?stream=","streamTokenApiUrl":"http:\/\/www.rtbf.be\/api\/media\/streaming","streamTokenApiUrlFC":"http:\/\/token.rtbf.be\/","logApiUrl":"http:\/\/www.rtbf.be\/api\/media\/log\/player"}

"""