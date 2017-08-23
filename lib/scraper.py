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

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

import common
import api
import utils

@common.plugin.cached(common.cachetime_programs)
def get_programs():
    
    """
    Get the list of shows
    TO FIX we should find the API for this
    """
    
    common.plugin.log("scraper.get_programs()")
    
    response = utils.request_url('https://www.rtbf.be/auvio/emissions')
    if not response:
        return
    
    soup = BeautifulSoup(response,'html.parser')

    nodes = soup.select('.rtbf-media-item')
    
    items = []

    for node in nodes:
        item = {}
        item['id'] = node['data-id']
        link = node.find('a', {'class': 'www-faux-link'})
        item['name'] = link['title'].encode('utf-8').strip()
        items.append(item)

    return items


@common.plugin.cached(common.cachetime_medias_recent)
def get_channel_recent_medias(id,page=1):
    """
    Get a list of recent medias by channel ID
    TO FIX this should be replaced by an API call; but can't find its endpoint...
    """
    
    items = []
    
    channel = api.get_single_channel_by_id(id)
    channel_url = channel.get('links',{}).get('auvio_replay',None)

    common.plugin.log("scraper.get_channel_recent_medias()")
    
    response = utils.request_url(channel_url)
    if not response:
        return items

    soup = BeautifulSoup(response,'html.parser')
    html_nodes = soup.select('a.www-faux-link')

    for html_node in html_nodes:
        link_url = html_node['href']
        media_id = utils.get_media_id_from_url(link_url)

        if not media_id:
            continue

        item = api.get_media_details(media_id)
        
        if not item:
            continue

        items.append(item)

    return items




@common.plugin.cached(common.cachetime_medias_recent)
def get_radio_recent_podcasts(id,page=1):
    
    items = []
    
    channel = api.get_single_channel_by_id(id)
    channel_slug = channel.get('key','')
    
    if not channel_slug:
        return items
    
    podcasts_url = 'http://rss.rtbf.be/media/rss/audio/{0}_recent.xml'.format(channel_slug)
    
    response = utils.request_url(podcasts_url)
    if not response:
        return items
    
    soup = BeautifulSoup(response,'html.parser')
    xml_nodes = soup.findAll('item')
    
    for xml_node in xml_nodes:
        
        #datetime
        pubdate = xml_node.find('pubdate').string.encode('utf-8').strip()
        pubdate = utils.datetime_to_W3C(pubdate)
        
        #duration
        duration_str = xml_node.find('itunes:duration').string.encode('utf-8').strip()
        duration = utils.convert_podcast_duration(duration_str)

        podcast_item = {
            'title':        xml_node.find('title').string.encode('utf-8').strip(),
            'description':  xml_node.find('description').string.encode('utf-8').strip(),
            'pubdate':      pubdate,
            'stream_url':   xml_node.find('enclosure')['url'].encode('utf-8').strip(),
            'duration':     duration,
            'image':        xml_node.find('itunes:image')['href'].encode('utf-8').strip(),
        }

        items.append(podcast_item)

    return items


@common.plugin.cached(common.cachetime_medias_recent)
def get_selection():
    """
    Return the medias from 'Notre Selection' on the Auvio homepage
    """
    
    items = []

    common.plugin.log("scraper.get_selection()")
    
    response = utils.request_url(common.auvio_url)
    if not response:
        return items

    soup = BeautifulSoup(response,'html.parser')
    html_nodes = soup.select('#widget-ml-notreselection-mediahomemedia a.www-faux-link')

    for html_node in html_nodes:
        link_url = html_node['href']
        media_id = utils.get_media_id_from_url(link_url)
        
        item = api.get_media_details(media_id)
        
        if not item:
            continue

        items.append(item)

    return items
    
    