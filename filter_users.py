import json
import os

# 文件路径
users_json_path = "./users.json"
user_txt_path = "./user.txt"
output_json_path = "./users_fix.json"

# 读取user.txt文件中的昵称列表
allowed_nicknames = set()
try:
    with open(user_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            nickname = line.strip()
            if nickname:  # 忽略空行
                allowed_nicknames.add(nickname)
    print(f"从user.txt中读取了{len(allowed_nicknames)}个昵称")
except FileNotFoundError:
    print(f"错误: 找不到文件 {user_txt_path}")
    exit(1)

# 读取users.json文件
try:
    with open(users_json_path, 'r', encoding='utf-8') as f:
        users_data = json.load(f)
except FileNotFoundError:
    print(f"错误: 找不到文件 {users_json_path}")
    exit(1)
except json.JSONDecodeError:
    print(f"错误: {users_json_path} 不是有效的JSON文件")
    exit(1)

# 过滤用户
original_count = len(users_data['rows'])
filtered_rows = []

for user in users_data['rows']:
    if user['nickname'] in allowed_nicknames:
        filtered_rows.append(user)

# 更新用户数据
users_data['rows'] = filtered_rows
users_data['total'] = len(filtered_rows)

# 保存到新文件
try:
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)
    
    removed_count = original_count - len(filtered_rows)
    print(f"处理完成: 原有{original_count}个用户，保留{len(filtered_rows)}个用户，删除{removed_count}个用户")
    print(f"结果已保存到: {output_json_path}")
except Exception as e:
    print(f"保存文件时出错: {str(e)}")