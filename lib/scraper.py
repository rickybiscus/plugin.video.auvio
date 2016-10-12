#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
Scraper for the Auvio website, used when we don't have the API methods
"""

import os
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
from bs4 import BeautifulSoup
import urlparse

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

import common
import api
import utils

def parse_media_el(media_el):
    
    """
    Fetch media informations from the API from HTML media blocks
    """
    
    common.plugin.log('scraper.parse_media_el')
    common.plugin.log(media_el)
    
    #get url
    media_link = media_el.select('a.www-faux-link')[0]
    media_url = media_link.get('href',None)
    common.plugin.log('found media url:'+media_url)

    #get ID
    media_url_parsed = urlparse.urlparse(media_url)
    media_id = urlparse.parse_qs(media_url_parsed.query)['id'][0]
    common.plugin.log('found media ID#'+media_id)

    #try to define media type
    media_type = None
    
    play_icon_el = media_el.select('.www-media-type i') #grid items having a sound icon
    if len(play_icon_el):
        play_icon_classes = play_icon_el[0].get("class")
        if 'ico-volume' in play_icon_classes:
             media_type = 'audio'

    if not media_type:
        media_classes = media_el.get("class")
        if 'rtbf-media-li--audio' in media_classes: #recent items
             media_type = 'audio'

    #get media details
    item = api.get_media_details(media_id,media_type)
    common.plugin.log('media details :')
    common.plugin.log(json.dumps(item))

    return item    
    

    
@common.plugin.cached(common.cachetime_live)
def get_live_videos():
    """
    parse live page and fetch every live video
    """
    items = []
    
    url = common.auvio_url + 'direct'
    html_doc = utils.request_url(url)
    soup = BeautifulSoup(html_doc,'html.parser')
    blocks = soup.select(".rtbf-media-grid .rtbf-media-item")
    
    common.plugin.log('scraper.get_live_videos')
    common.plugin.log('found %d blocks' % len(blocks))

    for media_el in blocks:
        #Transform the HTML element into a media similar to auvio> /api/emissions-medias

        common.plugin.log('make api media from HTML:')
        common.plugin.log(media_el)

        #link
        link_el = media_el.select('.rtbf-media-item__title a')[0]
        
        #title
        title = link_el.getText().strip()
        subtitle = media_el.select('.rtbf-media-item__subtitle')
        if subtitle and len(subtitle):
            subtitle = subtitle[0].getText().strip()

        #get channel
        channel_el = media_el.select('.rtbf-media-item__channel')[0]
        channel_el.span.decompose() #remove the live label el '.www-live--label'
        channel_name = channel_el.getText().strip()

        #get image
        image_el = media_el.find(lambda tag: tag.name == 'img' and 'data-srcset' in tag.attrs)

        media = {
            'id':               media_el.get('data-id',None),
            'type':             'live',
            'title':            title,
            'subtitle':         subtitle,
            'description':      None,
            'channel':          channel_name,
            'date':             None,
            'date_w3c':         media_el.get('data-begin',None),
            'expire':           None,
            'expire_w3c':       None,
            'imageSrcSet':      image_el.get('data-srcset',None),
            'duration':         None,
            'url':              link_el.get('href',None),
            'remainingDays':    None,
            'remainingHours':   None,
            #add custom keys
            'cat_id':          media_el.get('data-category',None)

        }

        common.plugin.log(json.dumps(media))
        items.append(media)

    common.plugin.log(json.dumps(items))
    return items


@common.plugin.cached(common.cachetime_live)
def get_live_radios():
    """
    parse live page and fetch every live radio
    """
    items = []
    
    url = common.auvio_url + 'direct'
    html_doc = utils.request_url(url)
    soup = BeautifulSoup(html_doc,'html.parser')
    blocks = soup.select(".js-popup-live-radio")
    
    common.plugin.log('scraper.get_live_radio')
    common.plugin.log('found %d blocks' % len(blocks))

    for media_el in blocks:
        #Transform the HTML element into a media similar to auvio> /api/emissions-medias

        common.plugin.log('make api media from HTML:')
        common.plugin.log(media_el)

        #get url
        url = media_el.get('href')
        common.plugin.log('radio url:'+url)

        #get slug
        radio_slug = os.path.basename(os.path.normpath(url))
        common.plugin.log('radio slug:'+radio_slug)

        #get config.json
        data = api.get_live_radio_config(radio_slug)

        #get show titles
        title = media_el.select('.rtbf-channel-item__title')[0].getText().strip()
        subtitle = media_el.select('.rtbf-channel-item__subtitle')[0].getText().strip()

        #get image
        image_el = media_el.find(lambda tag: tag.name == 'img' and 'data-srcset' in tag.attrs)

        media = {
            'id':               data.get('currentStationID'),
            'type':             'radio',
            'title':            title,
            'subtitle':         subtitle,
            'description':      None,
            'channel':          radio_slug,
            'date':             None,
            'date_w3c':         None,
            'expire':           None,
            'expire_w3c':       None,
            'imageSrcSet':      image_el.get('data-srcset',None),
            'duration':         None,
            'url':              url,
            'remainingDays':    None,
            'remainingHours':   None
        }

        common.plugin.log(json.dumps(media))
        items.append(media)

    common.plugin.log(json.dumps(items))
    return items

@common.plugin.cached(common.cachetime_category_medias)
def get_category_medias(id):
    
    """
    parse category page and fetch media blocks
    """
    
    items = []
    url = common.auvio_url + 'categorie/?id=%s' % id
    common.plugin.log('scraper.get_category_medias: %s (%s)' % (id,url))

    html_doc = utils.request_url(url)
    soup = BeautifulSoup(html_doc,'html.parser')
    
    blocks = soup.select(".rtbf-media-item")

    for media_el in blocks:
        item = parse_media_el(media_el)
        items.append(item)

    return items


@common.plugin.cached(common.cachetime_channel_medias)
def get_channel_medias(channel_id,type):
    
    """
    parse channel page and fetch media blocks (recent, selection, shows)
    """
    
    items = []
    channel_url = utils.get_channel_attr(channel_id,'url')
    
    common.plugin.log('scraper.get_channel_medias (%s) for channel#%s' % (type,channel_id))
    common.plugin.log('url:'+channel_url)
    
    html_doc = utils.request_url(channel_url)
    soup = BeautifulSoup(html_doc,'html.parser')

    if type=='recent':
        blocks = soup.select('section.rtbf-epg-side article')
    elif type=='selection':
        blocks = soup.select("section.row.rtbf-media-grid article")
    elif type=='shows':
        blocks = soup.select("section.js-item-container article")

    for media_el in blocks:
        item = parse_media_el(media_el)
        items.append(item)

    
    return items

"""
def get_live_video_url(lid):
    common.plugin.log("get_live_rtmp for ID#" + lid)
    
    url = utils.get_live_embed_url(lid)
    html_doc = utils.request_url(url)
    
    soup = BeautifulSoup(html_doc,'html.parser')
    player = soup.select("#js-embed-player")[0]
    data = player.get('data-media')
    data = json.loads(data)
    
    url = data.get('streamUrlHls')
    
    common.plugin.log(json.dumps(data))
    
    return url
"""