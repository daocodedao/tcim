from scrape_new import getNewsArray
from sendGroupMsg import sendMsg
from openai import OpenAI
import schedule
import time
import random
import json
from utils.logger_settings import api_logger

openAiClient = OpenAI(base_url="http://39.105.194.16:6691/v1", api_key="key")

groupIds = [
    "73225880",
    "15989378",
    "23342946",
    "10961043",
    "14236862",
    "71628838",
    "11372931",
    "97380810",
]

def jobGetMsgAndSend():
    api_logger.info(f"开始获取新闻，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    newsList = getNewsArray()

    newsTitles = []
    for news in newsList:
        newsTitles.append(news[1])
        
    newsTitles = newsTitles[:30]    
    prompt = f"""
                你需要从新闻标题中，生成适合聊天的话题。要求如下
                1. 话题主要是在群聊里使用，最好是问句，问句不要只针对一个人，比如 你对xxx 怎么看。要改为 你们觉得xxxx
                2. 话题的长度不超过30个汉字
                3. 不适合生成话题的新闻可以跳过
                4. 话题是中文的
                5. 最少生成20个话题
                6. 话题要口语化，不要太严肃

                以下是新闻标题:
                {newsTitles}
                
                请以 JSON 格式返回结果，格式如下, 不要做任何解释，只返回json:
                {{
                    "topics": ["中文话题1", "中文话题2", "..."]
                }}
                """    
        
    response = openAiClient.chat.completions.create(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=[
            {
                "role": "system",
                "content": "你是一个聊天助手，从各种新闻标题中，生成各种适合聊天的话题。",
            },
            {"role": "user", "content": prompt},
        ],
    )

    result = response.choices[0].message.content
    api_logger.info(f"生成的话题: {result}")
    
    try:
        # 解析JSON结果
        topics_data = json.loads(result)
        topics = topics_data.get("topics", [])
        
        if not topics:
            api_logger.error("未能获取到有效话题")
            return
        
        # 开始发送消息到各个群
        # api_logger.info(f"话题：{topics}")
        send_topics_to_groups(topics)
    except json.JSONDecodeError:
        api_logger.error(f"JSON解析错误: {result}")
    except Exception as e:
        api_logger.error(f"发生错误: {str(e)}")

def send_topics_to_groups(topics):
    """将话题发送到各个群组，每隔1-3分钟发送一条"""
    api_logger.info(f"开始发送话题到群组，共{len(topics)}个话题")
    
    # 确保话题数量足够
    if len(topics) < len(groupIds):
        # 如果话题不够，重复使用
        topics = topics * (len(groupIds) // len(topics) + 1)
    
    # 随机打乱话题顺序
    random.shuffle(topics)
    
    # 为每个群组分配一个话题
    for i, group_id in enumerate(groupIds):
        if i >= len(topics):
            break
            
        topic = topics[i]
        # 随机等待1-3分钟
        wait_time = random.randint(60, 180)
        api_logger.info(f"将在{wait_time}秒后发送到群组{group_id}: {topic}")
        
        # 等待指定时间
        time.sleep(wait_time)
        
        # 发送消息
        try:
            sendMsg(group_id, topic)
            api_logger.info(f"成功发送到群组{group_id}: {topic}")
        except Exception as e:
            api_logger.info(f"发送到群组{group_id}失败: {str(e)}")

def run_daily_job():
    """每天早上10点执行任务"""
    schedule.every().day.at("10:00").do(jobGetMsgAndSend)
    
    api_logger.info("定时任务已设置，将在每天早上10:00执行")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 如果需要立即执行一次，可以取消下面的注释
    jobGetMsgAndSend()
    
    # 启动定时任务
    run_daily_job()
    
   
