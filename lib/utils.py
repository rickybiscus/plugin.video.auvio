#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import xbmc
import xbmcaddon
import datetime
import time
import dateutil.parser
import urllib2

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

import common
import api


def request_url(url, referer='http://www.google.com'):
    common.plugin.log('request_url : %s' % url)
    req = urllib2.Request(url)
    req.addheaders = [('Referer', referer),
            ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100101 Firefox/11.0 ( .NET CLR 3.5.30729)')]
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def datetime_W3C_to_kodi(input):
    if input is None:
        common.plugin.log_error('utils.datetime_W3C_to_kodi() : no input')
        return None
    
    #CONVERT datetime (ISO9601) to kodi format (01.12.2008)
    date_obj = dateutil.parser.parse(input)
    return date_obj.strftime('%d.%m.%Y')

def timestamp_to_kodi(timestamp):
    """
    Converts a timestamp to kodi format (01.12.2008)
    """
    date_obj = datetime.datetime.fromtimestamp(int(timestamp))
    return date_obj.strftime('%d.%m.%Y')

def datetime_to_W3C(input = None):
    """
    Converts a date string from eg. 2016-09-12T13:00:00+02:00 to eg. '12.09.2016'
    """
    if not input:
        input = datetime.datetime.now()
    return input.isoformat()

def convert_duration_str(input):
    """
    Converts a date string from eg. '5min 35s' to eg. '6'
    """
    
    if not input:
        common.plugin.log_error('utils.convert_duration_str() : no input')
        return
    
    seconds = 0
    try:
        matches = re.search("(\d+)min (\d+)s",input)
        if matches:
            m = int(matches.groups()[0]) * 60
            s = int(matches.groups()[1])
            seconds = m + s
    except:
        common.plugin.log_error('utils.convert_duration_str() : error converting duration: ' + str(input))
        pass
    
    return seconds

def get_srcset_image(srcSet,key=1):
    
    """
    Returns image URL from a srcSet (from API or scraper)
    """
    
    #keys : 0=SD, 1=MD, 2=HD
    
    images = []
    
    if not srcSet:
        common.plugin.log_error('utils.get_srcset_image() : no input')
        return
    
    #make sure this is a list
    if not isinstance(srcSet, list):
        srcSet = srcSet.split(',')

    for single_img_str in srcSet:
        
        img_split = single_img_str.strip().split(' ')

        if len(img_split) < 2:
            continue    
            
        img = {
            'url':  img_split[0],
            'size': img_split[1]
        }
        
        images.append(img)

    #get size
    for i,image in enumerate(images):
        if i == key:
            return image.get('url')

def get_live_embed_url(lid):
    return common.auvio_url + 'embed/direct?id=%s&autoplay=1' % lid

def get_channel_attr(id,attr):
    channels = api.get_channels()
    
    for channel in channels:
        channel_id = channel.get('id',None)
        if id == channel_id:
            return channel.get(attr,None)
        
def media_label(title=None,subtitle=None,channel_slugs=None):
    labels = []
    label = ''
    
    if title:
        title = '[B]' + title +'[/B]'
        
    if subtitle:
        title = title + ' - ' + subtitle
        
    labels.append(title)
        
    if channel_slugs:
        channels_names = []
        if not isinstance(channel_slugs, list):
            channel_slugs = [channel_slugs]
            
        for channel_slug in channel_slugs:
            channel = api.get_single_channel_by_name(channel_slug)
            if channel and ('name' in channel):
                channel_name = channel.get('name')
            else:
                channel_name = channel_slug

            channels_names.append(channel_name)
        channel_str = ', '.join(channels_names)
        labels.append(channel_str)
      
    labels = filter(None, labels)
    label = ' | '.join(labels)
    
    return label