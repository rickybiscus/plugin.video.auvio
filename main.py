#!/usr/bin/python
# -*- coding: utf-8 -*-

# Module: main
# Author: R.Biscus
# Created on: 04.10.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

#documentation about log levels : https://alwinesch.github.io/group__python__xbmc.html#ga3cd3eff2195727144ad6fbabd4744961

import os
import xbmcvfs
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
import re
import math
import urllib.request
import urllib.parse
import time
import inputstreamhelper

# Add the /lib folder to sys TOUFIX TOUCHECK needed ?
sys.path.append(xbmcvfs.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

# SimplePlugin
from lib.simpleplugin import Addon

# Plugin modules
from lib import common
from lib import api
from lib import utils
from lib import gigya
from lib import redbee

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
        common.plugin.log("get_user_jwt_token - missing email or password",xbmc.LOGWARNING)
        raise ValueError("Veuillez configurer votre compte dans les options de l'addon.")

    else:

        user_login = Addon().get_setting('email')
        user_pwd = Addon().get_setting('password')

        session = gigya.get_user_session(user_login,user_pwd)
        uid = session['UID']

        #user_datas = gigya.get_account_info(uid)
        user_token = gigya.get_jwt(uid)

        if not user_token:

            common.plugin.log("get_user_jwt_token - unable to get user token",xbmc.LOGERROR)
            raise ValueError("Impossible de récupérer le token utilisateur.")
            return #TOFIX TOCHECK do we need a to return here ?

        else:

            return user_token

@common.plugin.route('/')
def root():

    #direct
    url = common.plugin.url_for('menu_live')
    li = xbmcgui.ListItem('En direct')
    li.setArt({'thumb': 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(handle=common.plugin.handle, url=url, listitem=li, isFolder=True)

    #accueil
    url = common.plugin.url_for('menu_homepage')
    li = xbmcgui.ListItem('Accueil')
    li.setArt({'thumb': 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(handle=common.plugin.handle, url=url, listitem=li, isFolder=True)

    #chaines
    url = common.plugin.url_for('menu_channels')
    li = xbmcgui.ListItem('Chaînes')
    li.setArt({'thumb': 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(handle=common.plugin.handle, url=url, listitem=li, isFolder=True)

    #categories
    url = common.plugin.url_for('menu_categories')
    li = xbmcgui.ListItem('Catégories')
    li.setArt({'thumb': 'DefaultFolder.png'})
    xbmcplugin.addDirectoryItem(handle=common.plugin.handle, url=url, listitem=li, isFolder=True)

    #TOUFIX
    #account
    # url = common.plugin.url_for('menu_favorites')
    # li = xbmcgui.ListItem('Mon Auvio')
    # li.setArt({'thumb': 'DefaultFolder.png'})
    # xbmcplugin.addDirectoryItem(handle=common.plugin.handle, url=url, listitem=li, isFolder=True)

    # xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/menu_single_channel/<channel_id>/<channel_type>/<sidebar_id>')
def menu_single_channel(**params):

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

    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)


@common.plugin.route('/menu_single_category/<category_id>/<sidebar_id>')
def menu_single_category(**params):

    listing = []
    cid = int(params.get('category_id',0))
    sid = int(params.get('sidebar_id',0)) #to get the channel 'sections' (called widgets in Auvio)

    if sid:
        sidebar_listing = get_sidebar_listing(sid)
        listing += sidebar_listing

    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/menu_categories')
def menu_categories():

    datas = api.get_menu_categories()
    listing = categories_to_items(datas)
    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)


@common.plugin.route('/menu_favorites')
def menu_favorites():

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
                list_item = media_to_kodi_item(media_node)
                url = list_item.getPath()
                listing.append((url, list_item))

        xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
        xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/list_widget_block_items/<widget_id>/<block_id>')
def list_widget_block_items(**params):

    wid = int(params.get('widget_id',0))
    bid = int(params.get('block_id',0))

    listing = []

    #widget sections
    widget_details = api.get_widget_detail(wid)
    widget_metas = widget_details.get('widget_meta')
    widget_blocks = widget_details.get('widget_blocks')

    section_metas = widget_metas[bid]
    blocks = widget_blocks[bid]
    blocks_content = blocks.get('content',[])

    #BLOCK ITEMS
    for item in blocks_content:
        list_item = media_to_kodi_item(item)
        url = list_item.getPath()
        listing.append((url, list_item))

    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)


@common.plugin.route('/menu_channels')
def menu_channels():

    datas = api.get_menu_channels()
    listing = channels_to_items(datas)
    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/menu_live')
def menu_live():

    datas = api.get_live_videos()
    listing = live_videos_to_items(datas)

    sortable_by = (xbmcplugin.SORT_METHOD_DATE,
                   xbmcplugin.SORT_METHOD_DURATION)

    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/menu_homepage')
def menu_homepage():
    listing = []
    sid = '3669' #home sidebar

    sidebar_listing = get_sidebar_listing(sid)
    listing += sidebar_listing

    xbmcplugin.addDirectoryItems(common.plugin.handle, listing, len(listing))
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(common.plugin.handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.endOfDirectory(common.plugin.handle)

@common.plugin.route('/play_radio/<channel_id>')
def play_radio(**params):

    cid = int(params.get('channel_id',None))
    media_url = None

    common.plugin.log("play_radio #{0}".format(cid),xbmc.LOGINFO)

    channel = api.get_single_channel(cid)

    if channel:
        stream_node = channel.get('streamurl',None)

        if stream_node:
            media_url = stream_node.get('mp3','').encode('utf-8').strip()

    if media_url:
        #play

        liz = xbmcgui.ListItem(path=media_url)
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

    else:

        common.plugin.log("unable to get the radio stream URL.",xbmc.LOGERROR)
        common.popup("Impossible de trouver le flux radio")


@common.plugin.route('/play_media/<media_id>/<livevideo>')
def play_media(**params):

    mid = int(params.get('media_id',None))
    is_livevideo = ( params.get('livevideo','') == 'True' )

    common.plugin.log("play media #{0} - live:{1}".format(mid,is_livevideo),xbmc.LOGINFO)

    #get media details
    media = api.get_media_details(mid,is_livevideo)
    media_type = media.get('type')
    has_drm = media.get('drm')

    common.plugin.log("media #{0} datas: {1}".format(mid,json.dumps(media)),xbmc.LOGINFO)

    #get media stream URL
    media_url = None
    media_drmlicense = None
    media_data = None
    
    # for old media using the old API
    stream_node = media.get('url_streaming')

    if stream_node:

        if media_type == 'audio':
            media_url = stream_node.get('url','').strip()

        elif is_livevideo and not utils.media_is_streaming(media):
            #do nothing since stream has not yet began
            pass
        else:
            media_url = stream_node.get('url_hls','').strip()

            if has_drm:

                #DRM-bypass using HLS (HTTP Live Streaming)
                """
                We are not able yet to play the DRM protected streams through KODI (should be okay in Kodi Leia).
                Meanwhile, hack the url_hls property to get a DRM-free stream
                (Like the 'urlHlsAes128' property returned by https://www.rtbf.be/api/media/video/?method=getVideoDetail&args[]=MEDIAIDHERE)
                See also https://github.com/rickybiscus/plugin.video.auvio/pull/16/commits/d20e370650abbd5f63e333646bea70b1be05298d

                (DRM code for further use:)

                #get user token
                try:
                    user_token = get_user_jwt_token()
                except ValueError as e:
                    common.popup(e)  # warn user
                    return False  # TOFIX how to cancel media play ?

                #get base64 licence
                auth = api.get_drm_media_auth(user_token, mid, is_livevideo)
                common.plugin.log("media #{0} auth: {1}".format(mid,auth),xbmc.LOGINFO)
                """

                # live
                if "_drm.m3u8" in media_url:
                    media_url = media_url.replace('_drm.m3u8','_aes.m3u8')
                # VOD
                elif "master.m3u8" in media_url:
                    media_url = media_url.replace('/master.m3u8','-aes/master.m3u8')
    
    else:
        # Get RTBF JSON Web Token
        common.plugin.log("Before rtbf_login()",xbmc.LOGINFO)

        if not user_has_account():
            common.plugin.log("get_user_jwt_token - missing email or password",xbmc.LOGWARNING)
            raise ValueError("Veuillez configurer votre compte dans les options de l'addon.")
        else:
            user_login = Addon().get_setting('email')
            user_pwd = Addon().get_setting('password')
        
        rtbf_login_data = redbee.rtbf_login(user_login, user_pwd)
        rtbf_jwt = redbee.get_rtbf_jwt(rtbf_login_data['sessionInfo']['cookieValue'])
        
        # Get RedBee JSON Web Token
        redbee_jwt = redbee.get_redbee_jwt(rtbf_jwt['id_token'])

        # Get media URL
        media_data = redbee.get_redbee_media_url(mid, redbee_jwt['sessionToken'])        
        if "mediaLocator" in media_data:
            media_url = media_data['mediaLocator']
            if "drm" in media_data:
                media_drmlicense = media_data['drm']['com.widevine.alpha']['licenseServerUrl']
                common.plugin.log("media #{0} drm license: {1}".format(mid,media_drmlicense),xbmc.LOGINFO)

    if media_url:

        common.plugin.log("media #{0} stream url: {1}".format(mid,media_url),xbmc.LOGINFO)

        #build playable item
        liz = xbmcgui.ListItem(path=media_url)

        if media_drmlicense:
            is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
            if is_helper.check_inputstream():
                liz.setProperty('inputstream', is_helper.inputstream_addon)
                liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                liz.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                liz.setProperty('inputstream.adaptive.license_key', media_drmlicense + '||R{SSM}|')

        #return playable item
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)

    else:
        common.plugin.log("unable to get stream URL.",xbmc.LOGERROR)
        common.popup("Impossible de trouver le flux media")



@common.plugin.route('/download_media')
def download_media(params):

    from slugify import slugify

    #validate path
    download_folder = Addon().get_setting('download_folder')

    if not download_folder:
        common.popup("Veuillez configurer un répertoire de téléchargement dans les paramètres du plugin")
        common.plugin.log("download_media: No directory set",xbmc.LOGERROR)
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
        common.plugin.log("unable to get a downloadable stream URL.",xbmc.LOGERROR)
        common.popup("Impossible de trouver un flux media téléchargeable")
        return False

    #filename
    remote_path = urllib.parse.urlparse(media_url).path #full path
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
    file_path = urllib.parse.unquote(file_path)

    common.plugin.log("download_media #{0} - filename:{1} - from:{2}".format(mid,file_name,media_url),xbmc.LOGINFO)

    # Overwrite existing file?
    if os.path.isfile(file_path):

        do_override = common.ask('Le fichier [B]%s[/B] existe déjà.  Écraser ?' % (file_name))

        if not do_override:
            return

    # Download
    size = 1024 * 1024
    start = time.clock()
    f = open(file_path, 'wb')
    request = urllib.request.Request(media_url)
    response = urllib.request.urlopen(request)
    bytes_so_far = 0
    error = False

    # Get file size
    try:
        total_size = response.info().getheader('Content-Length').strip()
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

            buff = response.read(size)
            if not buff:
                break
            else:
                bytes_so_far += len(buff)
                f.write(buff)

                percent = min(100 * bytes_so_far / total_size, 100)
                speed_str = str(int((bytes_so_far / 1024) / (time.clock() - start))) + ' KB/s'
                percent_str = str(percent) + '%'
                progressdialog.update(percent, file_name,percent_str,speed_str)

        except Exception as e:
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

    list_items = []

    #get sidebar widgets
    widgets = api.get_sidebar_widget_list(sid)

    common.plugin.log("getting every widget item for sidebar #%s..." % (sid),xbmc.LOGINFO)

    if widgets:
        for widget in widgets:

            #widget sections
            wid = int(widget.get('id',0))
            widget_details = api.get_widget_detail(wid)
            widget_blocks = widget_details.get('widget_blocks')
            blocks_count = len(widget_blocks)

            if blocks_count:

                current_block = 0;
                while current_block < blocks_count:

                    try:
                        blocks = widget_blocks[current_block]
                    except IndexError:
                        current_block += 1
                        break;

                    blocks_metas = blocks.get('meta',[])
                    blocks_content = blocks.get('content',[])

                    label = blocks_metas.get('title','')
                    label2 = blocks_metas.get('subtitle','')
                    url = common.plugin.url_for('list_widget_block_items',widget_id=wid,block_id=current_block)

                    list_item = xbmcgui.ListItem(label)
                    list_item.setLabel2(label2)
                    list_items.append((url, list_item, True))  #True = is virtual folder

                    current_block += 1

    common.plugin.log("...finished getting widgets for sidebar #%s" % (sid),xbmc.LOGINFO)

    return list_items

def get_subradio_listing(cid):

    # Get the KODI audio streams for a radio channel.

    list_items = []

    url_params = {
        'id':   cid
    }
    subchannels = api.get_channel_list(url_params)

    if subchannels:
        for channel in subchannels:

            cid = channel.get('id',None)

            label = channel.get('name').encode('utf-8').strip()
            url = common.plugin.url_for('play_radio',channel_id=cid)
            thumb = channel.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370',None).encode('utf-8').strip()
            fanart = channel.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080',None).encode('utf-8').strip()

            list_item = xbmcgui.ListItem(label)
            list_item.setPath(url)
            list_item.setProperty('isPlayable', 'true')
            list_item.setInfo('music',{})
            list_item.setArt({ 'thumb': thumb, 'fanart' : fanart })
            list_items.append((url, list_item, False))  #True = is virtual folder


    return list_items

def channels_to_items(datas):
    list_items = []

    if datas:
        for data in datas:

            cid = int(data.get('id',0))
            ctype = data.get('type')
            sid = int(data.get('sidebar_id',0))

            label = data.get('label','').encode('utf-8')
            url = common.plugin.url_for('menu_single_channel',channel_id=cid,channel_type=ctype,sidebar_id=sid)

            list_item = xbmcgui.ListItem(label)
            list_items.append((url, list_item, True))  #True = is virtual folder

    return list_items

def categories_to_items(datas):
    list_items = []

    if datas:
        for data in datas:
            cid = int(data.get('id',0))
            sid = int(data.get('sidebar_id',0))
            label = data.get('label','')
            url = common.plugin.url_for('menu_single_category',category_id=cid,sidebar_id=sid)

            list_item = xbmcgui.ListItem(label)
            list_items.append((url, list_item, True))  #True = is virtual folder

    return list_items

def live_videos_to_items(datas):
    list_items = []

    if datas and len(datas):
        for data in datas:
            li = media_to_kodi_item(data)
            url = li.getPath()
            list_items.append((url, li, False))

    return list_items


def media_to_kodi_item(media):

    #MEDIA
    mid = media.get('id')
    media_type = media.get('type')
    is_livevideo = (media_type == 'livevideo')
    kodi_type = utils.get_kodi_media_type(media)
    has_drm = media.get('drm')
    channel_node = media.get('channel')

    #props
    label = media.get('title','').strip()
    label2 = media.get('subtitle','').strip()
    context_actions = [] #context menu actions

    if channel_node:
        channel = channel_node.get('label','').strip()
        label = "[B]{0}[/B] - {1}".format(channel,label)

    if label2:
        label = "{0} - [I]{1}[/I]".format(label,label2)

    #Add 'DRM' prefix
    if has_drm and Addon().get_setting('drm_title_prefix'):
        label = "[COLOR red]DRM[/COLOR] " + label

    #live video
    if is_livevideo:
        if utils.media_is_streaming(media):
            label += ' [COLOR yellow]direct[/COLOR]'
        else:
            stream_start = utils.get_stream_start_date_formatted(media.get('start_date',None))
            label += ' [COLOR red]' + stream_start + '[/COLOR]'


    #MEDIA INFOS
    #http://romanvm.github.io/script.module.simpleplugin/_actions/vf.html
    #http://kodi.wiki/view/InfoLabels#ListItem

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

    elif kodi_type=='music':
        music_infos = {
            'genre':        media.get('category',{}).get('label').encode('utf-8'),
        }

        #parse args
        info_details = utils.parse_dict_args(info_details,music_infos)

    #download context menu
    if not is_livevideo and not has_drm:
        download_action = (
            'Télécharger',
            'XBMC.RunPlugin(%s)' % common.plugin.url_for('download_media',media_id=mid)
        )
        context_actions.append(download_action)

    thumb = media.get('images',{}).get('cover',{}).get('1x1',{}).get('370x370','').encode('utf-8').strip()
    fanart = media.get('images',{}).get('illustration',{}).get('16x9',{}).get('1920x1080','').encode('utf-8').strip()
    url = common.plugin.url_for('play_media',media_id=mid,livevideo=is_livevideo)

    list_item = xbmcgui.ListItem(label)
    list_item.setLabel2(label2)
    list_item.setPath(url)
    list_item.setProperty('isPlayable', 'true')
    list_item.setInfo(kodi_type,info_details)
    list_item.setArt({ 'thumb': thumb, 'fanart' : fanart })
    list_item.addContextMenuItems(context_actions)

    return list_item

# Start plugin from within Kodi.
if __name__ == "__main__":
    # Map actions
    # Note that we map callable objects without brackets ()
    common.plugin.run()
