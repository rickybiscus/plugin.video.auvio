#!/usr/bin/python
# -*- coding: utf-8 -*-

# Module: main
# Author: R.Biscus
# Created on: 04.10.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
import re
import math
import urllib2
import urlparse
import time

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

# Plugin modules
import common
import scraper
import api
import gigya
import utils

from simpleplugin import Addon

# initialize_gettext
#_ = common.plugin.initialize_gettext()
 
@common.plugin.action()
def root(params):
    
    listing = []
    
    listing.append({
        'label':    'En direct',
        'url':     common.plugin.get_url(action='list_medias',filter_medias='live_medias_recent'),
    })

    listing.append({
        'label':    'Chaînes',
        'url':      common.plugin.get_url(action='list_channels')
    })

    listing.append({
        'label':    'Émissions',
        'url':      common.plugin.get_url(action='list_programs')
    })
    
    listing.append({
        'label':    'Catégories',
        'url':      common.plugin.get_url(action='list_categories')
    })
    
    listing.append({
        'label':    'Sélection',
        'url':      common.plugin.get_url(action='list_selection')
    })
    
    if user_has_account():
    
        listing.append({
            'label':    'Mon Auvio',
            'url':      common.plugin.get_url(action='list_favorites')
        })


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

    channel_id = int(params.get('id',0))
    page = int(params.get('page',1))

    channel = api.get_single_channel_by_id(channel_id)
    channel_slug = channel.get('key')
    channel_thumb = channel.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip()
    channel_fanart = channel.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip()
    listing = []
    
    common.plugin.log("menu_single_channel")
    common.plugin.log(json.dumps(channel))

    type = channel.get('type',None)
    
    if type=='tv':
        
        #current live channel media
        media_node = api.get_channel_current_live(channel_slug)
        if media_node:
            live_item = media_to_kodi_item(media_node,{'show_channel':False})
            listing.append(live_item)
            
        #recent live medias
        media_nodes = scraper.get_channel_recent_medias(channel_id,page)
        if media_nodes:
            for media_node in media_nodes:
                li = media_to_kodi_item(media_node,{'show_channel':False})
                listing.append(li)  # Item label
            
    elif type=='radio' or type=='webradio':
        
        #radio stream
        live_item = radio_stream_to_kodi_item(channel,{'show_type':False})
        live_item['label'] += ' [COLOR yellow]direct[/COLOR]'
        listing.append(live_item)
        
        #recent podcasts
        recent_podcasts = scraper.get_radio_recent_podcasts(channel_id,page)
        if recent_podcasts:
            for podcast in recent_podcasts:
                li = podcast_to_kodi_item(podcast)
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
def list_categories(params):
    
    listing = []
    
    categories = api.get_menu_categories()

    if categories:
        for item in categories:
            li = category_to_kodi_item(item)
            listing.append(li)  # Item label
        
    sortable_by = (
        xbmcplugin.SORT_METHOD_LABEL
    )

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
def list_selection(params):
    
    listing = []
    
    nodes = scraper.get_selection()

    if nodes:
        for media_node in nodes:
            li = media_to_kodi_item(media_node)
            listing.append(li)  # Item label
        
    sortable_by = (
        xbmcplugin.SORT_METHOD_LABEL
    )

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
def list_favorites(params):
    
    user_login = Addon().get_setting('email')
    user_pwd = Addon().get_setting('password')
    
    session = gigya.get_user_session(user_login,user_pwd)
    uid = session['UID']
    
    #user_datas = gigya.get_account_info(uid)
    user_token = gigya.get_jwt(uid)
    
    nodes =  api.get_user_favorites(user_token)
    
    if nodes:
        for media_node in nodes:
            li = media_to_kodi_item(media_node)
            listing.append(li)  # Item label
        
    sortable_by = (
        xbmcplugin.SORT_METHOD_LABEL
    )

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
def list_channels(params):
    
    listing = []
    
    channels = api.get_channels()

    if channels:
        for channel in channels:
            li = channel_to_kodi_item(channel)
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
def list_medias(params):
    
    common.plugin.log("list_medias")
    common.plugin.log(json.dumps(params))
    
    filter_medias = params.get('filter_medias','')
    page =          int(params.get('page',1))
    channel_id =    int(params.get('channel_id',0))
    category_id =   int(params.get('category_id',0))
    program_id =    int(params.get('program_id',0))

    nodes = []
    listing = []
    listing_params = {}

    #live
    if filter_medias == 'live_medias_recent':
        nodes = api.get_live_videos(page)
    #program
    elif filter_medias == 'program_medias_recent':
        nodes = api.get_program_medias(program_id,page)
        listing_params['show_channel'] = False
    #category
    elif filter_medias == 'category_medias_recent':
        nodes = api.get_category_medias(category_id,page)

    if nodes and len(nodes):
        for node in nodes:
            li = media_to_kodi_item(node,listing_params)
            listing.append(li)  # Item label

    #menu link
    link_root = navigate_root()
    listing.append(link_root)
    
    #pagination link if the listing is not empty
    if nodes and len(nodes):
        link_next = next_medias_link(params)
        if link_next:
            listing.append(link_next)
    
    sortable_by = (xbmcplugin.SORT_METHOD_DATE,
                   xbmcplugin.SORT_METHOD_DURATION)

    return common.plugin.create_listing(
        listing,
        succeeded = True, #if False Kodi won’t open a new listing and stays on the current level.
        #update_listing = False, #if True, Kodi won’t open a sub-listing but refresh the current one. 
        #cache_to_disk = True, #cache this view to disk.
        #sort_methods = sortable_by, #he list of integer constants representing virtual folder sort methods.
        #view_mode = None, #a numeric code for a skin view mode. View mode codes are different in different skins except for 50 (basic listing).
        #content = None #string - current plugin content, e.g. ‘movies’ or ‘episodes’.
    )


@common.plugin.action()
def list_programs(params):
    
    listing = []
    shows = scraper.get_programs()
    
    if shows:
        for item in shows:        
            li = program_to_kodi_item(item)
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



@common.plugin.action()
def stream_url(params):
    
    url = params.get('url',None)
    common.plugin.log("stream_url() url:%s" % (url))

    if not url:
        common.popup("Impossible de lire ce flux")
        plugin.log_error("Impossible de lire ce flux")
        return
        
    liz = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

@common.plugin.action()
def download_media(params):
    
    from slugify import slugify
    
    title=  params.get('title');
    url=    params.get('url');
    
    #validate path
    download_folder = Addon().get_setting('download_folder')
    
    if not download_folder:
        common.popup("Veuillez configurer un répertoire de téléchargement dans les paramètres du plugin")
        common.plugin.log_error("download_media: No directory set")
        return False

    if not url:
        common.popup("Impossible de télécharger ce média")
        plugin.log_error("download_media: Missing URL")
        return False

    #filename
    remote_path = urlparse.urlparse(url).path #full path
    remote_file = url.rsplit('/', 1)[-1] #only what's after the last '/'
    remote_filename = os.path.splitext(remote_file)[0]
    remote_ext = os.path.splitext(remote_file)[1]
    
    file_name = slugify(title) + remote_ext
    file_path = xbmc.makeLegalFilename(os.path.join(download_folder, file_name))
    file_path = urllib2.unquote(file_path)

    common.plugin.log('download_media - filename: %s from %s' % (file_name,url))
    
    # Overwrite existing file?
    if os.path.isfile(file_path):
        
        do_override = common.ask('Le fichier [B]%s[/B] existe déjà.  Écraser ?' % (file_name)) 

        if not do_override:
            return

    # Download
    size = 1024 * 1024
    start = time.clock()
    f = open(file_path, 'wb')
    u = urllib2.urlopen(url)
    bytes_so_far = 0
    error = False

    # Get file size
    try:
        total_size = u.info().getheader('Content-Length').strip()
        total_size = int(total_size)
    except AttributeError:
        total_size = 0 # a response doesn't always include the "Content-Length" header
        
    if total_size < 1:
        common.popup("Erreur lors du téléchargement: Impossible de déterminer la taille du fichier.")
        return False
    
    # Progress dialog
    progressdialog = xbmcgui.DialogProgress()
    progressdialog.create("Téléchargement du média...") #Title

    while True:
        
        # Aborded by user
        if (progressdialog.iscanceled()):
            error = True
            break
        
        try:
            
            buff = u.read(size)
            if not buff:
                break
            else:
                bytes_so_far += len(buff)
                f.write(buff)

                percent = min(100 * bytes_so_far / total_size, 100)
                speed_str = str(int((bytes_so_far / 1024) / (time.clock() - start))) + ' KB/s'
                percent_str = str(percent) + '%'
                progressdialog.update(percent, file_name,percent_str,speed_str)
                    
        except Exception, e:
            error = True
            break
            
    f.close()
            
    if error:
        common.popup("Erreur lors du téléchargement.")
    else:
        progressdialog.update(100, "Terminé!")
        xbmc.sleep(1000)
        
    progressdialog.close()

def context_action_download(title,url):
    return (
        'Télécharger', 
        'XBMC.RunPlugin(%s)' % common.plugin.get_url(action='download_media',title=title,url=url)
    )

def channel_to_kodi_item(node):
    """
    Convert a channel API object to a kodi list item
    """

    label = node.get('name','').encode('utf-8').strip()
    label = "{0} - [I]{1}[/I]".format(label,node.get('type'))
    
    channel_type = node.get('type',None)
    channel_url = ''
    
    has_submenu = True

    channel_url = node.get('links',{}).get('auvio_channel',None)
    channel_id = utils.get_url_arg(channel_url,'id')

    if channel_id != str(node.get('id')):
        has_submenu = False
            
    if not has_submenu and (channel_type == 'webradio' or channel_type == 'radio'):
        
        li = radio_stream_to_kodi_item(node)
        li['label'] += ' [COLOR yellow]direct[/COLOR]'
        
    else:
        
        channel_url = common.plugin.get_url(action='menu_single_channel',id=node.get('id'))

        li = {
            'label':    label,
            #'label2':   node.get('type'),
            'url':      channel_url,
            'thumb':    node.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip(),
            'fanart':   node.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip(),
        }
        
    return li

def radio_stream_to_kodi_item(node,args={}):
    
    """
    Convert a channel API object to a kodi list item
    """
    
    label = node.get('name','').encode('utf-8').strip()
    
    if args.get('show_type',True):
        label = "{0} - [I]{1}[/I]".format(label,node.get('type'))

    channel_url = ''
    


    #stream URL
    media_url = ''
    stream_node = node.get('streamurl',None)
    if stream_node:
        media_url = stream_node.get('mp3','').encode('utf-8').strip()
        channel_url = common.plugin.get_url(action='stream_url',url=media_url)

    li = {
        'label':    label,
        #'label2':   node.get('type'),
        'url':      channel_url,
        'thumb':    node.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip(),
        'fanart':   node.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip(),
        'is_playable':  True
    }
 
    return li

def category_to_kodi_item(node):
    
    id = int(node.get('id',0))
    
    """
    Convert a category API object to a kodi list item
    """
    
    li = {
        'label':    node.get('label',''),
        'url':      common.plugin.get_url(action='list_medias',filter_medias='category_medias_recent',category_id=id)
    }
    return li

def program_to_kodi_item(node):
    
    """
    Convert a show API object to a kodi list item
    """
    
    id = int(node.get('id',0))

    li = {
        'label':    node.get('name',''),
        'url':      common.plugin.get_url(action='list_medias',filter_medias='program_medias_recent',program_id=id),
        #'thumb':    image, # Item thumbnail
        #'fanart':   image,
        'info': {
            'video': { ##http://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
                #'plot':         node.get('description',''),#Long Description
                #'plotoutline':  node.get('description',''),#Short Description
            }
        }

    }
    return li

def media_to_kodi_item(node,args={}):
    
    context_actions = [] #context menu actions

    #build label
    title = node.get('title','').encode('utf-8').strip()
    subtitle = node.get('subtitle','').encode('utf-8').strip()
    channel_node = node.get('channel',)

    label = title
    
    if args.get('show_channel',True) and channel_node:
        channel = channel_node.get('label','').encode('utf-8').strip()
        if channel:
            label = "[B]{0}[/B] - {1}".format(channel,label)
    
    if subtitle:
        label = "{0} - [I]{1}[/I]".format(label,subtitle)

    if node.get('type') == 'livevideo':
        if utils.is_live_media(node):
            label += ' [COLOR yellow]direct[/COLOR]'
        else:
            stream_start = utils.get_stream_start_date_formatted(node.get('start_date',None))
            label += ' [COLOR red]' + stream_start + '[/COLOR]'

    #kodi type
    media_type = node.get('type')
    
    #media infos
    #http://romanvm.github.io/script.module.simpleplugin/_actions/vf.html
    #http://kodi.wiki/view/InfoLabels#ListItem
    
    infos = {
        'date':         utils.datetime_W3C_to_kodi(node.get('start_date')),
        #'aired':        utils.datetime_W3C_to_kodi(node.get('start_date')),
        'count':        node.get('id'),
        'duration':     int(round(args.get('duration',0))),
    }
    
    if media_type=='video' or media_type=='livevideo':
        kodi_type = 'video'
        infos_video = {
            'genre':        node.get('category',{}).get('label').encode('utf-8'),
            'plot':         node.get('description','').encode('utf-8'),#Long Description
            'plotoutline':  node.get('description','').encode('utf-8'),#Short Description
        }
        infos.update(infos_video) #merge arrays
        
        
    if media_type=='audio' or media_type=='radio':
        kodi_type = 'music'
        infos_audio = {
            'genre':        node.get('category',{}).get('label').encode('utf-8'),
        }
        infos.update(infos_audio) #merge arrays
        
    #stream URL
    media_url = ''
    stream_node = node.get('url_streaming')

    if media_type=='livevideo' and utils.is_live_media(node): #TO FIX maybe show teaser insetad nothing ?
        if stream_node:
            media_url = stream_node.get('url_hls','').encode('utf-8').strip()
            
    elif media_type=='video' or media_type=='audio':
        if stream_node:
            media_url = stream_node.get('url','').encode('utf-8').strip()
        if media_url: #Download
            
            if subtitle:
                file_title = "%s - %s" % (title,subtitle)
            else:
                file_title = title

            action_download =  context_action_download(file_title,media_url)
            context_actions.append(action_download)

    li = {
        'label':    label,
        'thumb':    node.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip(),
        'fanart':   node.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip(),
        'url':      common.plugin.get_url(action='stream_url',url=media_url),
        'info': {
            kodi_type: infos
        },
        'is_playable':  True,
        'context_menu': context_actions
    }

    return li

def podcast_to_kodi_item(node,args={}):
    
    context_actions = [] #context menu actions
    
    #media URL
    media_url = node.get('stream_url','')
    
    #Download
    if media_url:
        file_title = node.get('title')
        action_download =  context_action_download(file_title,media_url)
        context_actions.append(action_download)
    
    li = {
        'label':    node.get('title'),
        'thumb':    node.get('image',''),
        'url':      common.plugin.get_url(action='stream_url',url=media_url),
        'info': {
            'music': {
                'date':         node.get('pubdate'),
                #'aired':        utils.datetime_W3C_to_kodi(node.get('start_date')),
                'duration':     node.get('duration',''),
            }
        },
        'is_playable':  True,
        'context_menu': context_actions
    }

    return li

def next_medias_link(params):
    
    filter_medias = params.get('filter_medias','')
    page =          int(params.get('page',1))
    channel_id =    int(params.get('channel_id',0))
    category_id =   int(params.get('category_id',0))
    program_id =    int(params.get('program_id',0))
    
    next_page = page + 1 

    title = ".. Page suivante (%d)" % (next_page)

    link = {
        'label':    title,
        'url':      common.plugin.get_url(
                        action=         'list_medias',
                        page=           next_page,
                        filter_medias=  filter_medias,
                        channel_id=     channel_id,
                        category_id=    category_id,
                        program_id=     program_id,
                    )
    }
    
    return link

def navigate_root():
    return {
        'label':    ".. Retour au menu principal",
        'url':      common.plugin.get_url(action='root')
    }

def user_has_account():
    user_login = Addon().get_setting('email')
    user_pwd = Addon().get_setting('password')
    
    if user_login and user_pwd:
        return True
    else:
        return False




# Start plugin from within Kodi.
if __name__ == "__main__":
    # Map actions
    # Note that we map callable objects without brackets ()
    common.plugin.run()