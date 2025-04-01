#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import base64
import hmac
import hashlib
import requests
import zlib
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量获取SDK配置信息
sdk_app_id = int(os.getenv('SDK_APP_ID', ''))
secret_key = os.getenv('SECRET_KEY', '')
admin_identifier = os.getenv('ADMIN_IDENTIFIER', '123456')

group_id = os.getenv('GROUP_ID', '73225880')
message_text = os.getenv('MESSAGE_TEXT', 'ETH能到2000吗？')

# 生成UserSig
def gen_user_sig(sdk_appid, user_id, key, expire=180*86400):
    """
    生成UserSig
    :param sdk_appid: 应用的SDKAppID
    :param user_id: 用户ID
    :param key: 密钥
    :param expire: 过期时间，默认为180天
    :return: UserSig
    """
    current_time = int(time.time())
    expire_time = current_time + expire
    
    obj = {
        "TLS.ver": "2.0",
        "TLS.identifier": user_id,
        "TLS.sdkappid": sdk_appid,
        "TLS.expire": expire,
        "TLS.time": current_time
    }
    
    string_to_sign = ''
    for key, value in sorted(obj.items()):
        string_to_sign += key + ':' + str(value) + '\n'
    
    hmac_obj = hmac.new(key.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256)
    sig = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    
    obj['TLS.sig'] = sig
    
    json_str = json.dumps(obj)
    compressed = json_str.encode('utf-8')
    
    return base64.b64encode(compressed).decode('utf-8')

def base64_encode_url(data):
    """ base url encode 实现"""
    base64_data = base64.b64encode(data)
    base64_data_str = bytes.decode(base64_data)
    base64_data_str = base64_data_str.replace('+', '*')
    base64_data_str = base64_data_str.replace('/', '-')
    base64_data_str = base64_data_str.replace('=', '_')
    return base64_data_str

def __hmacsha256(sdk_appid, identifier, secret_key, curr_time, expire, base64_userbuf=None):
    """ 通过固定串进行 hmac 然后 base64 得的 sig 字段的值"""
    raw_content_to_be_signed = "TLS.identifier:" + str(identifier) + "\n"\
                                + "TLS.sdkappid:" + str(sdk_appid) + "\n"\
                                + "TLS.time:" + str(curr_time) + "\n"\
                                + "TLS.expire:" + str(expire) + "\n"
    if None != base64_userbuf:
        raw_content_to_be_signed += "TLS.userbuf:" + base64_userbuf + "\n"
    return base64.b64encode(hmac.new(secret_key.encode('utf-8'),
                                        raw_content_to_be_signed.encode('utf-8'),
                                        hashlib.sha256).digest())

def __gen_sig(sdk_appid, identifier, secret_key, expire=180*86400, userbuf=None):
    """ 用户可以采用默认的有效期生成 sig """
    curr_time = int(time.time())
    m = dict()
    m["TLS.ver"] = "2.0"
    m["TLS.identifier"] = str(identifier)
    m["TLS.sdkappid"] = sdk_appid
    m["TLS.expire"] = int(expire)
    m["TLS.time"] = int(curr_time)
    base64_userbuf = None
    if None != userbuf:
        base64_userbuf = bytes.decode(base64.b64encode(userbuf))
        m["TLS.userbuf"] = base64_userbuf

    m["TLS.sig"] = bytes.decode(__hmacsha256(sdk_appid, 
                                             secret_key,
                                             identifier, 
                                             curr_time, 
                                             expire, 
                                             base64_userbuf))

    raw_sig = json.dumps(m)
    sig_cmpressed = zlib.compress(raw_sig.encode('utf-8'))
    base64_sig = base64_encode_url(sig_cmpressed)
    return base64_sig

# 发送群组消息
def send_group_message(sdk_appid, admin_id, user_sig, group_id, message_text):
    """
    发送群组消息
    :param sdk_appid: 应用的SDKAppID
    :param admin_id: 管理员ID
    :param user_sig: UserSig
    :param group_id: 群组ID
    :param message_text: 消息内容
    :return: 响应结果
    """
    random = int(time.time())
    # Changed the API endpoint from console.tim.qq.com to the correct one

    url = f"https://console.tim.qq.com/v4/group_open_http_svc/send_group_msg?sdkappid={sdk_appid}&identifier={admin_id}&usersig={user_sig}&random={random}&contenttype=json"
    
    # Try with the international endpoint if the above doesn't work
    # url = f"https://admin.tim.intl.im.qq.com/v4/group_open_http_svc/send_group_msg?sdkappid={sdk_appid}&identifier={admin_id}&usersig={user_sig}&random={random}&contenttype=json"
    
    payload = {
        "GroupId": group_id,
        "Random": random,
        "MsgBody": [
            {
                "MsgType": "TIMTextElem",
                "MsgContent": {
                    "Text": message_text
                }
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# 主函数
def main():
    # 生成UserSig
    user_sig = __gen_sig(sdk_app_id, 
                         admin_identifier, 
                         secret_key)
    user_sig1 = gen_user_sig(sdk_app_id, 
                         admin_identifier, 
                         secret_key)
    # 发送群组消息
    result = send_group_message(sdk_app_id, admin_identifier, user_sig, group_id, message_text)
    print(result)
    # 打印结果
    print(f"发送消息结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()