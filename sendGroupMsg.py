from timsdk import TimClient
import os


# 从环境变量获取SDK配置信息
sdk_app_id = os.getenv('SDK_APP_ID', '')
secret_key = os.getenv('SECRET_KEY', '')
admin_identifier = os.getenv('ADMIN_IDENTIFIER', '123456')


group_id = '73225880'  # 替换为你的群组ID
message_text = 'ETH能到2000吗？'

tim_client = TimClient(
    app_id=sdk_app_id,
    app_key=secret_key
)

result = tim_client.group_open_http_svc.send_group_msg(
    group_id=group_id,
    msg_body=[{
        "MsgType": "TIMTextElem",
        "MsgContent": {
            "Text": message_text
        }
    }])

print(result)