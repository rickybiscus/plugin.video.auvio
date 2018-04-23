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

# SimplePlugin
from simpleplugin import Addon

# Plugin modules
import common
import api
import utils
import gigya

# initialize_gettext
#_ = common.plugin.initialize_gettext()


def user_has_account():
    user_login = Addon().get_setting('email')
    user_pwd = Addon().get_setting('password')
    
    if user_login and user_pwd:
        return True
    else:
        return False

def get_user_jwt_token():
    #get the Gigya token for the current user
    #TOFIX should be cached in a way or another so we don't always call a new session ?
    
    if not user_has_account():
        common.plugin.log("get_user_jwt_token - missing email or password")
        raise ValueError("Veuillez configurer votre compte dans les options de l'addon.")
        
    else:
        
        user_login = Addon().get_setting('email')
        user_pwd = Addon().get_setting('password')

        session = gigya.get_user_session(user_login,user_pwd)
        uid = session['UID']

        #user_datas = gigya.get_account_info(uid)
        user_token = gigya.get_jwt(uid)
        
        if not user_token:
            
            common.plugin.log("get_user_jwt_token - unable to get user token")
            raise ValueError("Impossible de récupérer le token utilisateur.")
            return #TOFIX TOCHECK do we need a to return here ?
            
        else:
            
            return user_token
 
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
        
        #get user token
        try:
            user_token = get_user_jwt_token()
        except ValueError as e:
            common.popup(e) # warn user
            return

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
        li = media_to_kodi_item(item)
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
    live_medias = api.get_live_videos()
    
    if live_medias and len(live_medias):
        for live_media in live_medias:
            li = media_to_kodi_item(live_media)
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
def play_radio(params):
    
    cid = int(params.get('channel_id',None))
    media_url = None
    
    common.plugin.log("play_radio #{0}".format(cid))

    channel = api.get_single_channel(cid)
    
    if channel:
        common.plugin.log(json.dumps(channel))
        stream_node = channel.get('streamurl',None)

        if stream_node:
            media_url = stream_node.get('mp3','').encode('utf-8').strip()
        
    if not media_url:
        common.plugin.log_error("unable to get stream URL.")
        common.popup("Impossible de trouver le flux media")
        
    #play
    liz = xbmcgui.ListItem(path=media_url)
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

@common.plugin.action()
def play_media(params):
    mid = int(params.get('media_id',None))
    is_live = ( params.get('livemedia','') == 'True' )
    drm = ( params.get('drm','') == 'True' )
    
    common.plugin.log("play media #{0} - live:{1} - drm:{2}".format(mid,is_live,drm))

    #get media details
    media = api.get_media_details(mid,is_live)
    common.plugin.log("media #{0} datas: {1}".format(mid,json.dumps(media)))
    
    #get media stream URL
    media_url = None
    stream_node = media.get('url_streaming')
    
    if stream_node:
        #live media streaming - can be played without DRM licence
        if is_live and utils.media_is_streaming(media):
            media_url = stream_node.get('url_hls','').encode('utf-8').strip()
        else:
            #drm protected
            if drm:

                media_url = stream_node.get('url_hls','').encode('utf-8').strip()
                
                """
                Update drm-protected URL so it match the property 'urlHlsAes128' 
                at http://www.rtbf.be/api/media/video/?method=getVideoDetail&args[]=MEDIAIDHERE;
                which is DRM-free.
                """

                media_url = media_url.replace('/master.m3u8','-aes/master.m3u8')
                common.plugin.log("media #{0} drm-free stream url: {1}".format(mid,media_url))

            #regular media
            else:
                media_url = stream_node.get('url','').encode('utf-8').strip()

    if not media_url:
        common.plugin.log_error("unable to get stream URL.")
        common.popup("Impossible de trouver le flux media")
        return False #TOFIX how to cancel media play ?

    common.plugin.log("media #{0} stream url: {1}".format(mid,media_url))

    #build playable item
    liz = xbmcgui.ListItem(path=media_url)
    
    """
    #TOFIX WIP additional code for the DRMs (requires Kodi Leia) - commented as we don't need it yet; but keep it here so we don't forget it meanwhile.
    if drm:
        #get user token
        try:
            user_token = get_user_jwt_token()
        except ValueError as e:
            common.popup(e)  # warn user
            return False  # TOFIX how to cancel media play ?

        #get base64 licence
        auth = api.get_drm_media_auth(user_token, mid, is_live)
        common.plugin.log("media #{0} auth: {1}".format(mid,auth))
        
        #TOFIX!!!
        
    """

    #return playable item
    return xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

@common.plugin.action()
def download_media(params):
    
    from slugify import slugify
    
    #validate path
    download_folder = Addon().get_setting('download_folder')
    
    if not download_folder:
        common.popup("Veuillez configurer un répertoire de téléchargement dans les paramètres du plugin")
        common.plugin.log_error("download_media: No directory set")
        return False
    
    #get media details
    mid = int(params.get('media_id',None))
    media = api.get_media_details(mid)
    media_title = media.get('title')
    media_subtitle = media.get('subtitle')
    
    #media URL
    stream_node = media.get('url_streaming')

    if stream_node:
        media_url = stream_node.get('url','').encode('utf-8').strip()
        
    if not media_url:
        common.plugin.log_error("unable to get stream URL.")
        common.popup("Impossible de trouver le flux media")
        return False

    #filename
    remote_path = urlparse.urlparse(media_url).path #full path
    remote_file = media_url.rsplit('/', 1)[-1] #only what's after the last '/'
    remote_filename = os.path.splitext(remote_file)[0]
    remote_ext = os.path.splitext(remote_file)[1]
    
    if media_subtitle:
        file_title = "%s - %s" % (media_title,media_subtitle)
    else:
        file_title = media_title
        
    file_title = slugify(file_title)
        
    file_name = file_title + remote_ext
    file_path = xbmc.makeLegalFilename(os.path.join(download_folder, file_name))
    file_path = urllib2.unquote(file_path)

    common.plugin.log("download_media #{0} - filename:{1} - from:{2}".format(mid,file_name,media_url))
    
    # Overwrite existing file?
    if os.path.isfile(file_path):
        
        do_override = common.ask('Le fichier [B]%s[/B] existe déjà.  Écraser ?' % (file_name)) 

        if not do_override:
            return

    # Download
    size = 1024 * 1024
    start = time.clock()
    f = open(file_path, 'wb')
    u = urllib2.urlopen(media_url)
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
        if progressdialog.iscanceled():
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
            
            cid = channel.get('id',None)

            li = {
                'label':    channel.get('name').encode('utf-8').strip(),
                'url':      common.plugin.get_url(action='play_radio',channel_id=cid),
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

def media_to_kodi_item(media):
    
    #common.plugin.log(json.dumps(media))

    context_actions = [] #context menu actions
    
    #MEDIA
    mid = media.get('id')
    media_type = media.get('type')
    is_livemedia = (media_type == 'livevideo')
    kodi_type = utils.get_kodi_media_type(media)
    has_drm = media.get('drm')

    #build label
    title = media.get('title','').encode('utf-8').strip()
    subtitle = media.get('subtitle','').encode('utf-8').strip()
    channel_node = media.get('channel')

    if channel_node:
        channel = channel_node.get('label','').encode('utf-8').strip()
        title = "[B]{0}[/B] - {1}".format(channel,title)

    if subtitle:
        title = "{0} - [I]{1}[/I]".format(title,subtitle)
        
    #Add 'DRM' prefix
    if has_drm and Addon().get_setting('drm_title_prefix'):
        title = "[COLOR red]DRM[/COLOR] " + title

    #live video
    if is_livemedia:
        if utils.media_is_streaming(media):
            title += ' [COLOR yellow]direct[/COLOR]'
        else:
            stream_start = utils.get_stream_start_date_formatted(media.get('start_date',None))
            title += ' [COLOR red]' + stream_start + '[/COLOR]'


    #MEDIA INFOS
    #http://romanvm.github.io/script.module.simpleplugin/_actions/vf.html
    #http://kodi.wiki/view/InfoLabels#ListItem
    
    infos = {}
    info_details = {
        #'date':         utils.datetime_W3C_to_kodi(media.get('date_publish_from')), #file date
        'count':        media.get('id'), #can be used to store an id for later, or for sorting purposes
        'duration':     utils.get_kodi_media_duration(media),
    }
    
    if kodi_type=='video':
        
        video_infos = {
            'aired':        utils.datetime_W3C_to_kodi(media.get('date_publish_from')),
            'genre':        media.get('category',{}).get('label','').encode('utf-8'),
            'plot':         media.get('description','').encode('utf-8'),#Long Description
            'plotoutline':  media.get('description','').encode('utf-8'),#Short Description
        }
        
        #parse args
        info_details = utils.parse_dict_args(info_details,video_infos)
        
        infos = {
            'video': info_details
        }

    
    elif kodi_type=='music':
        music_infos = {
            'genre':        media.get('category',{}).get('label').encode('utf-8'),
        }
        
        #parse args
        info_details = utils.parse_dict_args(info_details,music_infos)
        
        infos = {
            'music': info_details
        }
 
    #download context menu
    if not is_livemedia and not has_drm:
        download_action = (
            'Télécharger', 
            'XBMC.RunPlugin(%s)' % common.plugin.get_url(action='download_media',media_id=mid)
        )
        context_actions.append(download_action)

    li = {
        'label':    title,
        'label2':   subtitle,
        'thumb':    media.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370','').encode('utf-8').strip(),
        'fanart':   media.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080','').encode('utf-8').strip(),
        'url':      common.plugin.get_url(action='play_media',media_id=mid,livemedia=is_livemedia,drm=has_drm),
        'info':     infos,
        'is_playable':  True,
        'context_menu': context_actions
    }

    return li

# Start plugin from within Kodi.
if __name__ == "__main__":
    # Map actions
    # Note that we map callable objects without brackets ()
    common.plugin.run()