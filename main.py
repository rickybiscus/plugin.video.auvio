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
        'url':     common.plugin.get_url(action='menu_live'),
    })
    
    listing.append({
        'label':    'Accueil',
        'url':     common.plugin.get_url(action='menu_homepage'),
    })

    listing.append({
        'label':    'Chaînes',
        'url':      common.plugin.get_url(action='menu_channels')
    })

    listing.append({
        'label':    'Catégories',
        'url':      common.plugin.get_url(action='menu_categories')
    })

    listing.append({
        'label':    'Mon Auvio',
        'url':      common.plugin.get_url(action='menu_favorites')
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

    listing = []
    sid = int(params.get('sidebar_id',0)) #to get the channel 'sections' (called widgets in Auvio)
    cid = int(params.get('channel_id',0))
    ctype = params.get('channel_type')

    if sid:
        sidebar_listing = get_sidebar_listing(sid)
        listing += sidebar_listing
        
    if ctype == 'radio':
        radio_listing = get_subradio_listing(cid)
        listing += radio_listing

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
def menu_single_category(params):
    
    listing = []
    sid = int(params.get('sidebar_id',0)) #to get the channel 'sections' (called widgets in Auvio)
    cid = int(params.get('category_id',0))
    
    if sid:
        sidebar_listing = get_sidebar_listing(sid)
        listing += sidebar_listing
    
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
def menu_categories(params):
    
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
def menu_favorites(params):
    
    if not user_has_account():
        
        common.popup("Veuillez configurer votre compte dans les options de l'addon.")
        
    else:
        
        listing = []

        user_login = Addon().get_setting('email')
        user_pwd = Addon().get_setting('password')

        session = gigya.get_user_session(user_login,user_pwd)
        uid = session['UID']

        #user_datas = gigya.get_account_info(uid)
        user_token = gigya.get_jwt(uid)

        favorites =  api.get_user_favorites(user_token)

        if favorites:
            for favorite in favorites:
                media_id = favorite.get('data',{}).get('id',0)
                media_node = api.get_media_details(media_id) #so we match the other API medias; because media_to_kodi_item can handle it - which is not the case of the current 'data' attribute. TOFIX TOCHECK.
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
def list_widget_section_items(params):
    
    wid = int(params.get('widget_id',0))
    sid = int(params.get('section_id',0))
    
    listing = []
    
    #widget sections
    widget_details = api.get_widget_detail(wid)
    widget_metas = widget_details.get('widget_meta')
    widget_blocks = widget_details.get('widget_blocks')

    section_metas = widget_metas[sid]
    blocks = widget_blocks[sid]
    blocks_metas = blocks.get('meta',[])
    blocks_content = blocks.get('content',[])

    #BLOCK ITEMS
    for item in blocks_content:
        li = media_to_kodi_item(item,{'show_channel':False})
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
def menu_channels(params):
    
    listing = []
    
    channels = api.get_menu_channels()

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
def menu_live(params):

    listing = []
    nodes = api.get_live_videos()
    
    if nodes and len(nodes):
        for node in nodes:
            li = media_to_kodi_item(node)
            listing.append(li)  # Item label

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
def menu_homepage(params):
    listing = []
    sid = '3669' #home sidebar

    sidebar_listing = get_sidebar_listing(sid)
    listing += sidebar_listing
    
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

def get_sidebar_listing(sid):
    
    # Get the KODI menu items for a sidebar.

    listing = []

    #get sidebar widgets
    widgets = api.get_sidebar_widget_list(sid)
    
    if widgets:
        for widget in widgets:
            
            #widget sections
            wid = int(widget.get('id',0))
            widget_details = api.get_widget_detail(wid)
            widget_metas = widget_details.get('widget_meta')
            widget_blocks = widget_details.get('widget_blocks')
            
            section_count = len(widget_metas);
            
            if section_count:
                current_section = 0;
                while current_section < section_count:
                    
                    try:
                        blocks = widget_blocks[current_section]
                    except IndexError:
                        current_section += 1
                        break;

                    #section_metas = widget_metas[current_section]
                    blocks_metas = blocks.get('meta',[])
                    blocks_content = blocks.get('content',[])

                    section_li = {
                        'label':        blocks_metas.get('title','').encode('utf-8'),
                        'label2':       blocks_metas.get('subtitle','').encode('utf-8'),
                        'url':          common.plugin.get_url(action='list_widget_section_items',widget_id=wid,section_id=current_section),
                        'is_folder':    True,
                    }

                    listing.append(section_li)
                    current_section += 1
                
    return listing

def get_subradio_listing(cid):
    
    # Get the KODI audio streams for a radio channel.

    listing = []
    
    url_params = {
        'id':   cid
    }
    subchannels = api.get_channel_list(url_params)
    
    if subchannels:
        for channel in subchannels:
            
            #stream URL
            channel_url = ''
            streamurl = channel.get('streamurl',None)
            if streamurl:
                media_url = streamurl.get('mp3','').encode('utf-8').strip()
                channel_url = common.plugin.get_url(action='stream_url',url=media_url)

            li = {
                'label':    channel.get('name').encode('utf-8').strip(),
                'url':      channel_url,
                'thumb':    channel.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip(),
                'fanart':   channel.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip(),
                'is_playable':  True
            }
            
            listing.append(li)
            
        return listing
            

def channel_to_kodi_item(channel):
    
    # Convert a category API object to a kodi list item
    
    cid = int(channel.get('id',0))
    ctype = channel.get('type')
    sid = int(channel.get('sidebar_id',0))
    label = channel.get('label','').encode('utf-8')

    li = {
        'label':    label,
        'url':      common.plugin.get_url(action='menu_single_channel',channel_id=cid,channel_type=ctype,sidebar_id=sid)
    }
    return li

def category_to_kodi_item(category):
    
    # Convert a category API object to a kodi list item
    
    cid = int(category.get('id',0))
    sid = int(category.get('sidebar_id',0))
    label = category.get('label','')

    li = {
        'label':    label,
        'url':      common.plugin.get_url(action='menu_single_category',category_id=cid,sidebar_id=sid)
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
            'genre':        node.get('category',{}).get('label','').encode('utf-8'),
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
        'thumb':    node.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370','').encode('utf-8').strip(),
        'fanart':   node.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080','').encode('utf-8').strip(),
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