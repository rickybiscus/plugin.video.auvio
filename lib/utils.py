#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import xbmc
import xbmcaddon
import json
import datetime
import time
import dateutil.parser
import dateutil.tz
import urllib2
import urlparse
import socket

# Add the /lib folder to sys
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

import common
import api


def request_url(url, referer='http://www.google.com'):
    common.plugin.log('request_url : %s' % url)
    req = urllib2.Request(url)
    req.addheaders = [('Referer', referer),('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100101 Firefox/11.0 ( .NET CLR 3.5.30729)')]

    try:
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
    except urllib2.URLError as e:
        common.plugin.log_error("Remote request error for URL %s: %r" % (url,e))
        return
    except socket.timeout, e:
        common.plugin.log_error("Remote request error for URL %s: %r" % (url,e))
        return

    return data

def now():
  return datetime.datetime.now(dateutil.tz.tzlocal())

def is_live_media(node):

    start_date = node.get('start_date',None)
    end_date = node.get('end_date',None)
    
    if not start_date or not end_date:
        common.plugin.log_error('utils.is_live_media() : missing start_date or end_date')
        return

    now_datetime = now()
    start_date = dateutil.parser.parse(start_date)
    end_date = dateutil.parser.parse(end_date)

    return (start_date <= now_datetime <= end_date)

def get_stream_start_date_formatted(start_date):
    
    if start_date is None:
        common.plugin.log_error('utils.is_live_media() : missing start_date')
        return None

    now_datetime = now()
    start_date = dateutil.parser.parse(start_date)
    
    formatted_date = start_date.strftime(xbmc.getRegion('dateshort'))
    formatted_time = start_date.strftime(xbmc.getRegion('time'))
    
    if now_datetime.date() != start_date.date():
        formatted_datetime = formatted_date + " - " + formatted_time
    else:
        formatted_datetime = formatted_time

    return formatted_datetime

def datetime_W3C_to_kodi(input):
    if input is None:
        common.plugin.log_error('utils.datetime_W3C_to_kodi() : no input')
        return None
    
    #CONVERT datetime (ISO9601) to kodi format (01.12.2008)
    date_obj = dateutil.parser.parse(input)
    return date_obj.strftime('%d.%m.%Y')

def datetime_to_W3C(input = None):
    """
    Converts a date string input to an ISO-8601 (W3C) string
    If no input is set, get current datetime
    """
    
    if not input:
        date = datetime.datetime.now()
    else:
        date = dateutil.parser.parse(input)

    return date.isoformat()

def convert_podcast_duration(time_str):
    """
    converts H:MM:SS to seconds
    """
    
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def get_url_arg(url,key,single = True):
    parsed = urlparse.urlparse(url)
    args = urlparse.parse_qs(parsed.query)

    if not key in args:
        return False

    if single:
        return args[key][0]
    else:
        return args[key]
