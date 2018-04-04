import json
import urllib
import common

#
import utils

# Gigya.com
gigya_api_key = '3_h1fE5zi6-OZoaLWFHHWQ2Qqs1vZrPW9dxqVAqvRwllmrOJn3Pmyt4w8Fa1KL-wEj'
gigya_api_secret = 'ptt4MTSi0FHgdVaQJSDrEUH8yDjlIhNW'
gigya_accounts_base_url = "https://accounts.eu1.gigya.com/accounts.";
gigya_api_key = "3_h1fE5zi6-OZoaLWFHHWQ2Qqs1vZrPW9dxqVAqvRwllmrOJn3Pmyt4w8Fa1KL-wEj";
gigya_secret = "ptt4MTSi0FHgdVaQJSDrEUH8yDjlIhNW";
gigya_socialize_base_url = "https://socialize.eu1.gigya.com/socialize.";
gigya_social_login_redirect_uri = "https://www.rtbf.be/app/auvio/android";
gigya_user_key = "APUBPn9ofPkV";

# retrieve Gigya user session
# TOFIX should be cached in a way or another so we don't request it over & over ?  For now, cache it for 5 minutes
# TOFIX should be cached ONLY if success !
# TOFIX use MemStorage ? http://romanvm.github.io/script.module.simpleplugin/storage.html
@common.plugin.cached(5)
def get_user_session(user_login,user_pwd):
    
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
    common.plugin.log('gigya get_user_session:')
    common.plugin.log(json_data)
    
    #no result
    if not json_data:
        common.plugin.log('gigya get_user_session: empty')
        return
    
    data = json.loads(json_data)
    
    #handle errors
    
    if 'errorMessage' in data:
        common.popup( 'gigya get_user_session: %s' % (data['errorMessage']) )
    
    if data['errorCode'] != 0:
        common.plugin.log("gigya get_user_session: error code #%s" % (json['errorCode']))
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_user_session: status code #%s" % (json['statusCode']))
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
        common.plugin.log('gigya get_account_info: empty')
        return
    
    data = json.loads(json_data)
    
    #handle errors
    if 'errorMessage' in data:
        common.popup( 'gigya get_account_info: %s' % (data['errorMessage']) )
        common.plugin.log( 'gigya get_account_info: %s' % (data['errorMessage']) )

    if data['errorCode'] != 0:
        common.plugin.log("gigya get_account_info: error code #%s" % (json['errorCode']))
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_account_info: status code #%s" % (json['statusCode']))
        return
    
    return data['userInfo']
  
def get_jwt(uid):
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
        common.plugin.log('gigya get_jwt: empty')
        return
    
    data = json.loads(json_data)
    
    #handle errors
    if 'errorMessage' in data:
        common.popup( 'gigya get_jwt: %s' % (data['errorMessage']) )
        common.plugin.log( 'gigya get_jwt: %s' % (data['errorMessage']) )

    if data['errorCode'] != 0:
        common.plugin.log("gigya get_jwt: error code #%s" % (json['errorCode']))
        return

    if data['statusCode'] != 200:
        common.plugin.log("gigya get_jwt: status code #%s" % (json['statusCode']))
        return
    
    return data['id_token']