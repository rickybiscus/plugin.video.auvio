import json
import urllib

# Plugin modules
from . import common
from . import utils

# Gigya.com
gigya_api_key = '3_h1fE5zi6-OZoaLWFHHWQ2Qqs1vZrPW9dxqVAqvRwllmrOJn3Pmyt4w8Fa1KL-wEj'
gigya_api_secret = 'ptt4MTSi0FHgdVaQJSDrEUH8yDjlIhNW'
gigya_accounts_base_url = "https://accounts.eu1.gigya.com/accounts.";
gigya_api_key = "3_h1fE5zi6-OZoaLWFHHWQ2Qqs1vZrPW9dxqVAqvRwllmrOJn3Pmyt4w8Fa1KL-wEj";
gigya_secret = "ptt4MTSi0FHgdVaQJSDrEUH8yDjlIhNW";
gigya_socialize_base_url = "https://socialize.eu1.gigya.com/socialize.";
gigya_social_login_redirect_uri = "https://www.rtbf.be/app/auvio/android";
gigya_user_key = "APUBPn9ofPkV";


def get_user_session(user_login,user_pwd):

    # retrieve Gigya user session

    url_params = {
        'loginID':  user_login,
        'password': user_pwd,
        'apiKey':   gigya_api_key,
        'userKey':  gigya_user_key,
        'secret':   gigya_secret,
        'format':   'json',
        'lang':     'fr',
    }
    url = gigya_accounts_base_url + 'login'

    json_data = utils.request_url(url,url_params)
    common.plugin.log('gigya get_user_session:',xbmc.LOGINFO)
    common.plugin.log(json_data,xbmc.LOGINFO)

    #no result
    if not json_data:
        common.plugin.log('gigya get_user_session: empty',xbmc.LOGINFO)
        return

    data = json.loads(json_data)

    #handle errors

    if 'errorMessage' in data:
        common.popup( 'gigya get_user_session: %s' % (data['errorMessage']) )

    if data['errorCode'] != 0:
        common.plugin.log("gigya get_user_session: error code #%s" % (json['errorCode']),xbmc.LOGERROR)
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_user_session: status code #%s" % (json['statusCode']),xbmc.LOGERROR)
        return

    return data

def get_account_info(uid):

    url_params = {
        'UID':      uid,
        'include':  'profile,userInfo',
        'apiKey':   gigya_api_key,
        'userKey':  gigya_user_key,
        'secret':   gigya_secret,
        'format':   'json',
        'lang':     'fr',
    }
    url = gigya_accounts_base_url + 'getAccountInfo'

    json_data = utils.request_url(url,url_params)

    #no result
    if not json_data:
        common.plugin.log('gigya get_account_info: empty',xbmc.LOGERROR)
        return

    data = json.loads(json_data)

    #handle errors
    if 'errorMessage' in data:
        common.popup( 'gigya get_account_info: %s' % (data['errorMessage']) )
        common.plugin.log( 'gigya get_account_info: %s' % (data['errorMessage']),xbmc.LOGERROR)

    if data['errorCode'] != 0:
        common.plugin.log("gigya get_account_info: error code #%s" % (json['errorCode']),xbmc.LOGERROR)
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_account_info: status code #%s" % (json['statusCode']),xbmc.LOGERROR)
        return

    return data['userInfo']

def get_jwt(uid):

    #get the Gigya token based on a user ID

    url_params = {
        'targetUID':    uid,
        'apiKey':       gigya_api_key,
        'userKey':      gigya_user_key,
        'secret':       gigya_secret,
        'format':       'json',
        'lang':         'fr',
    }
    url = gigya_accounts_base_url + 'getJWT'

    json_data = utils.request_url(url,url_params)

    #no result
    if not json_data:
        common.plugin.log('gigya get_jwt: empty',xbmc.LOGERROR)
        return

    data = json.loads(json_data)

    #handle errors
    if 'errorMessage' in data:
        common.popup( 'gigya get_jwt: %s' % (data['errorMessage']) )
        common.plugin.log( 'gigya get_jwt: %s' % (data['errorMessage']),xbmc.LOGERROR)

    if data['errorCode'] != 0:
        common.plugin.log("gigya get_jwt: error code #%s" % (json['errorCode']),xbmc.LOGERROR)
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_jwt: status code #%s" % (json['statusCode']),xbmc.LOGERROR)
        return

    return data['id_token']
