import json
import urllib
import xbmc

# Plugin modules
from . import common
from . import utils
# from urllib import request

# Variables 
gigya_api_key = '3_kWKuPgcdAybqnqxq_MvHVk0-6PN8Zk8pIIkJM_yXOu-qLPDDsGOtIDFfpGivtbeO'
redbee_customer = 'RTBF'
redbee_business_unit = 'Auvio'
redbee_base_url = f'https://exposure.api.redbee.live/v2/customer/{redbee_customer}/businessunit/{redbee_business_unit}'
redbee_gigyalogin_url = f'https://exposure.api.redbee.live/v2/customer/{redbee_customer}/businessunit/{redbee_business_unit}/auth/gigyaLogin'
rtbf_login_url = 'https://login.rtbf.be/accounts.login'
rtbf_login_cookie = f'glt_{gigya_api_key}'
rtbf_getJWT_url = 'https://login.rtbf.be/accounts.getJWT'
rtbf_unknown_id = '6BA97Bb'

# Functions
def rtbf_login(user_login, user_pwd):
    # common.plugin.log("rtbf_login()",xbmc.LOGINFO)
    
    url_params = {
        'loginID':  user_login,
        'password': user_pwd,
        'apiKey':   gigya_api_key,
        'format':   'json',
        'lang':     'fr'
    }
    
    response = utils.request_url(rtbf_login_url, url_params)
    
    if not response:
        common.plugin.log('rtbf_login response: empty')
        return
    
    data = json.loads(response)
    
    if 'errorMessage' in data:
        common.popup( 'rtbf_login errorMessage: %s' % (data['errorMessage']) )
    
    if data['errorCode'] != 0:
        common.plugin.log("rtbf_login errorCode: #%s" % (json['errorCode']),xbmc.LOGERROR)
        return
    
    if data['statusCode'] != 200:
        common.plugin.log("rtbf_login statusCode: #%s" % (data['statusCode']),xbmc.LOGERROR)
        return
    
    return data

def get_rtbf_jwt(login_token):
    # common.plugin.log("get_rtbf_jwt()",xbmc.LOGINFO)
    url_params = {
        'apiKey':       gigya_api_key,
        'login_token':  login_token,
        'format':       'json'
    }
    
    response = utils.request_url(rtbf_getJWT_url,url_params)
    
    if not response:
        common.plugin.log('get_rtbf_jwt response: empty')
        return
    
    data = json.loads(response)
    
    if 'errorMessage' in data:
        common.popup('rtbf_getJWT errorMessage: %s' % (data['errorMessage']))
    
    if data['errorCode'] != 0:
        common.plugin.log("rtbf_getJWT errorCode: #%s" % (data['errorCode']),xbmc.LOGERROR)
        return
    
    if data['statusCode'] != 200:
        common.plugin.log("rtbf_getJWT statusCode: #%s" % (data['statusCode']),xbmc.LOGERROR)
        return
    
    return data

def get_redbee_jwt(rtbf_jwt):
    # common.plugin.log("get_redbee_jwt()",xbmc.LOGINFO)
    url = redbee_base_url + '/auth/gigyaLogin'
    
    data_string = '{"jwt":"' + rtbf_jwt + '","device":{"deviceId":"123","name":"","type":"WEB"}}'
    data = data_string.encode("utf-8")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = utils.request_url(url, {}, headers, data)
    
    if not response:
        common.plugin.log('get_redbee_jwt response: empty',xbmc.LOGERROR)
        return
    
    data = json.loads(response)
        
    return data

def get_redbee_media_url(media_id, session_token):
    # common.plugin.log("get_redbee_media_url()",xbmc.LOGINFO)
    # url = redbee_base_url + f'/entitlement/{media_id}_{rtbf_unknown_id}/play'
    url = redbee_base_url + f'/entitlement/{media_id}/play'
    
    headers = {
        'Authorization': f'Bearer {session_token}'
    }
    
    response = utils.request_url(url, {}, headers)
    
    if not response:
        common.plugin.log('get_redbee_media_url response: empty',xbmc.LOGERROR)
        return
    
    data = json.loads(response)
    
    for fmt in data['formats']:
        if fmt['format'] == 'DASH':
            return fmt
    
    return ''
