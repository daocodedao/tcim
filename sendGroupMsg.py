
import os
from dotenv import load_dotenv
from utils.logger_settings import api_logger
from tencentcloud_im.tcim_client import TCIMClient, MessageText

load_dotenv()

# 从环境变量获取SDK配置信息
# print(os.getenv('SDK_APP_ID', ''))
sdk_app_id = int(os.getenv('SDK_APP_ID', ''))
secret_key = os.getenv('SECRET_KEY', '')
admin_identifier = os.getenv('ADMIN_IDENTIFIER', '')
# print(sdk_app_id, secret_key, admin_identifier)
fromAccount = "7274252717407870976"

# group_id = '73225880'  # 替换为你的群组ID
# message_text = 'ETH能到2000吗？'




# Changed the API endpoint from console.tim.qq.com to the correct one
SINGAPORE = "https://adminapisgp.im.qcloud.com/v4"
CHINA = "https://console.tim.qq.com/v4"
client = TCIMClient(sdk_app_id, 
                    secret_key, 
                    admin_identifier,
                    tencent_url=SINGAPORE)

def sendMsg(group_id, message_text):
    api_logger.info(f"sendMsg: {group_id}, {message_text}")
    msgTexgt = MessageText(message_text)
    result = client.send_group_message(group_id, 
                          messageText=[msgTexgt],
                          from_account=fromAccount)
    api_logger.info(result.content)