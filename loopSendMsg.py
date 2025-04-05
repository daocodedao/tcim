from scrape_new import getNewsArray
from sendGroupMsg import sendMsg
from openai import OpenAI
import schedule
import time
import random
import json
import os
import datetime
from utils.logger_settings import api_logger

openAiClient66 = OpenAI(base_url="http://39.105.194.16:6691/v1", api_key="key")
model66 = "Qwen/Qwen2.5-7B-Instruct"

openAiClient67 = OpenAI(base_url="http://39.105.194.16:9191/v1", api_key="key")
model67 = "qwen2.5:7b-instruct-fp16"

# 添加历史新闻存储路径
HISTORY_DIR = "./history_news"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def get_history_news():
    """获取历史新闻标题集合，并清理超过7天的历史记录"""
    history_titles = set()
    today = datetime.datetime.now().date()
    
    # 遍历历史文件
    for filename in os.listdir(HISTORY_DIR):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(HISTORY_DIR, filename)
        try:
            # 从文件名获取日期
            file_date_str = filename.split('.')[0]
            file_date = datetime.datetime.strptime(file_date_str, "%Y-%m-%d").date()
            
            # 如果文件超过7天，删除
            if (today - file_date).days > 7:
                os.remove(file_path)
                api_logger.info(f"删除过期历史新闻: {filename}")
                continue
                
            # 读取历史新闻
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for title in data:
                    history_titles.add(title)
        except Exception as e:
            api_logger.error(f"读取历史新闻文件出错: {str(e)}")
    
    return history_titles

def save_news_to_history(news_titles):
    """保存今天的新闻到历史记录"""
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(HISTORY_DIR, f"{today_str}.json")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(news_titles, f, ensure_ascii=False, indent=2)
        api_logger.info(f"保存今日新闻到历史记录: {len(news_titles)}条")
    except Exception as e:
        api_logger.error(f"保存历史新闻出错: {str(e)}")

def jobGetMsgAndSend():
    api_logger.info(f"开始获取新闻，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    newsList = getNewsArray()

    # 获取历史新闻
    history_titles = get_history_news()
    api_logger.info(f"历史新闻数量: {len(history_titles)}")
    
    # 去重新闻
    newsTitles = []
    unique_titles = []
    for news in newsList:
        title = news[1]
        newsTitles.append(title)
        if title not in history_titles:
            unique_titles.append(title)
    
    api_logger.info(f"获取新闻总数: {len(newsTitles)}, 去重后新闻数: {len(unique_titles)}")
    
    # 如果去重后没有新闻，使用原始新闻
    if not unique_titles:
        api_logger.info("去重后没有新闻，使用原始新闻")
        unique_titles = newsTitles
    
    # 保存今天的新闻到历史记录
    save_news_to_history(newsTitles)
    
    # 使用去重后的新闻
    unique_titles = unique_titles[:30]
    prompt = f"""
                你需要从新闻标题中，生成适合聊天的话题。要求如下
                . 每个新闻都只生产一个话题, 不适合生成话题的新闻可以跳过
                . 话题要口语化，不要太严肃
                . 话题主要是在群聊里使用，最好是问句
                . 问句可以用 你们觉得 你们看 你们怎么看 开头或结尾。也可以不用
                . 话题的长度不超过30个汉字
                . 话题是中文的
                . 最少生成20个话题
                . 不要出现 各种币价 涨跌预测，涨跌回顾，涨跌评价

                以下是新闻标题:
                {unique_titles}
                
                请以 JSON 格式返回结果，格式如下, 不要做任何解释，只返回json:
                {{
                    "topics": ["中文话题1", "中文话题2", "..."]
                }}
                """    
    
    # 添加异常处理和重试逻辑
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 首先尝试使用 openAiClient66
            api_logger.info("尝试使用 openAiClient66 生成话题")
            response = openAiClient66.chat.completions.create(
                model=model66,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个聊天助手，从各种新闻标题中，生成各种适合聊天的话题。",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            result = response.choices[0].message.content
            api_logger.info(f"成功使用 openAiClient66 生成话题")
            break
        except Exception as e:
            api_logger.error(f"使用 openAiClient66 生成话题失败: {str(e)}")
            try:
                # 尝试使用 openAiClient67
                api_logger.info("尝试使用 openAiClient67 生成话题")
                response = openAiClient67.chat.completions.create(
                    model=model67,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个聊天助手，从各种新闻标题中，生成各种适合聊天的话题。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                result = response.choices[0].message.content
                api_logger.info(f"成功使用 openAiClient67 生成话题")
                break
            except Exception as e2:
                api_logger.error(f"使用 openAiClient67 生成话题也失败: {str(e2)}")
                retry_count += 1
                if retry_count < max_retries:
                    api_logger.info(f"等待60秒后进行第{retry_count+1}次重试")
                    time.sleep(60)
                else:
                    api_logger.error("已达到最大重试次数，放弃生成话题")
                    return
    
    api_logger.info(f"生成的话题: {result}")
    
    try:
        # 解析JSON结果
        topics_data = json.loads(result)
        topics = topics_data.get("topics", [])
        
        if not topics:
            api_logger.error("未能获取到有效话题")
            return
        
        # 开始发送消息到各个群
        send_topics_to_groups(topics)
    except json.JSONDecodeError:
        api_logger.error(f"JSON解析错误: {result}")
    except Exception as e:
        api_logger.error(f"发生错误: {str(e)}")

def send_topics_to_groups(topics):
    """将话题发送到各个群组，每隔1-3分钟发送一条"""
    api_logger.info(f"开始发送话题到群组，共{len(topics)}个话题")
    
    # 读取群组信息
    try:
        with open("./group.json", "r", encoding="utf-8") as f:
            groups = json.load(f)
        api_logger.info(f"成功读取群组信息，共{len(groups)}个群组")
    except Exception as e:
        api_logger.error(f"读取群组信息失败: {str(e)}")
        return
    
    # 读取用户信息
    try:
        with open("./users_fix.json", "r", encoding="utf-8") as f:
            users = json.load(f)
        api_logger.info(f"成功读取用户信息，共{len(users)}个用户")
    except Exception as e:
        api_logger.error(f"读取用户信息失败: {str(e)}")
        return
    
    # 确保users是一个列表
    if isinstance(users, dict):
        users = list(users.values())
    
    # 随机打乱话题顺序
    random.shuffle(topics)
    
    # 为每个群组分配一个话题并生成聊天内容
    used_topics = set()  # 记录已使用的话题
    
    for group in groups:
        group_id = group["groupId"]
        group_name = group["groupName"]
        if not group_id:
            continue
            
        # 选择一个未使用的话题
        available_topics = [t for t in topics if t not in used_topics]
        if not available_topics:
            # 如果所有话题都已使用，重置已使用话题集合
            used_topics.clear()
            available_topics = topics
        
        topic = random.choice(available_topics)
        used_topics.add(topic)
        
        # 随机选择4-6个用户
        # 确保users是一个序列类型
        chat_users = random.sample(list(users), min(random.randint(4, 6), len(users)))
        
        try:
            # 生成聊天内容
            messages = generate_chat_content(topic, group_name, chat_users)
        
            # 发送聊天内容
            for i, message in enumerate(messages):
                sendMsg(group_id, message["content"], message["userId"])
                
                # 每条消息之间随机等待5-15秒
                time.sleep(random.randint(5, 15))
            api_logger.info(f"成功发送到群组{group_id}的聊天内容，话题: {topic}")
        except Exception as e:
            api_logger.error(f"发送到群组{group_id}失败: {str(e)}")

def generate_chat_content(topic, group_name, users):
    """使用OpenAI生成围绕话题的聊天内容"""
    api_logger.info(f"开始生成话题'{topic}'的聊天内容")
    
    # 提取用户信息，包括名称和性别
    user_infos = []
    for user in users:
        name = user.get("nickname", "未知用户")
        sex = "男" if user.get("sex") == 0 else "女"
        user_infos.append({"name": name, "sex": sex, "userId": user.get("childId", "未知用户ID")})
    
    prompt = f"""
    请生成一段围绕"{topic}"的群聊对话。要求如下：
    . 参与聊天的用户有: {user_infos}
    . 每个用户发言 1-3 次，整个对话至少有 7-12 次。其中可以有的发言可以简单些，1-3个字，也可以复杂些，10-20个字。
    . 用户发言要口语化，适合群组聊天
    . 用户发言要符合用户的性别
    . 所有用户都在群组里，群组名：{group_name}
    . 所有聊天群组话题都是有关币圈，虚拟币。不要讨论股市，不要讨论公司
    . 不要预测涨跌，不要回顾过去涨跌，不要评价市场走势，比如挺平稳，涨了不少，跌了很多之类。
    。 
    
    请以JSON格式返回结果，格式如下:
    {{
        "messages": [
            {{"user": "用户名1", "userId": "用户Id", "content": "消息内容1"}},
            {{"user": "用户名2", "userId": "用户Id", "content": "消息内容2"}},
            ...
        ]
    }}
    
    只返回JSON格式，不要有其他解释。
    """
    api_logger.info(prompt)
    
    # 添加异常处理和重试逻辑
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 首先尝试使用 openAiClient66
            api_logger.info("尝试使用 openAiClient66 生成聊天内容")
            response = openAiClient66.chat.completions.create(
                model=model66,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个聊天助手，负责生成真实、自然的群聊对话，需要考虑用户的性别特点。",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            result = response.choices[0].message.content
            api_logger.info(f"成功使用 openAiClient66 生成聊天内容")
            break
        except Exception as e:
            api_logger.error(f"使用 openAiClient66 生成聊天内容失败: {str(e)}")
            try:
                # 尝试使用 openAiClient67
                api_logger.info("尝试使用 openAiClient67 生成聊天内容")
                response = openAiClient67.chat.completions.create(
                    model=model67,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个聊天助手，负责生成真实、自然的群聊对话，需要考虑用户的性别特点。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                result = response.choices[0].message.content
                api_logger.info(f"成功使用 openAiClient67 生成聊天内容")
                break
            except Exception as e2:
                api_logger.error(f"使用 openAiClient67 生成聊天内容也失败: {str(e2)}")
                retry_count += 1
                if retry_count < max_retries:
                    api_logger.info(f"等待60秒后进行第{retry_count+1}次重试")
                    time.sleep(60)
                else:
                    api_logger.error("已达到最大重试次数，返回备用消息")
                    return [{"user": "系统", "userId": "", "content": f"大家都'{topic}'有什么看法？"}]
    
    try:
        # 解析JSON结果
        chat_data = json.loads(result)
        messages = chat_data.get("messages", [])
        return messages
    except Exception as e:
        api_logger.error(f"解析聊天内容JSON失败: {str(e)}")
        # 返回一个简单的备用消息
        return [{"user": "系统", "userId": "", "content": f"大家都'{topic}'有什么看法？"}]

def run_daily_job():
    """每天早上10点执行任务"""
    schedule.every().day.at("08:00").do(jobGetMsgAndSend)
    schedule.every().day.at("17:00").do(jobGetMsgAndSend)
    
    api_logger.info("定时任务已设置，将在每天早上10:00执行")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 如果需要立即执行一次，可以取消下面的注释
    # jobGetMsgAndSend()
    
    # 启动定时任务
    run_daily_job()
    
   
