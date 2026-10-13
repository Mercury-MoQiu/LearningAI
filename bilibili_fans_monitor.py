import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

# 直接使用UP主的UID，避免搜索
TARGET_UID = "213280180"
TARGET_NAME = "挖机牧魂人"
INTERVAL = 20

def get_fans_count():
    url = f"https://api.bilibili.com/x/relation/stat?vmid={TARGET_UID}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://space.bilibili.com/{}/'.format(TARGET_UID),
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            data = json.loads(data)
            if data.get('code') == 0:
                return data.get('data', {}).get('follower')
    except Exception as e:
        print(f"获取粉丝数失败: {e}")
    return None

def format_number(num):
    if num >= 10000:
        return f"{num/10000:.2f}万"
    return str(num)

def monitor_fans():
    print(f"开始监控UP主: {TARGET_NAME} (UID: {TARGET_UID})")
    print(f"监控周期: {INTERVAL}秒")
    print("-" * 50)
    
    while True:
        try:
            fans = get_fans_count()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if fans is not None:
                print(f"[{now}] {TARGET_NAME} 的实时粉丝数: {fans} ({format_number(fans)})")
            else:
                print(f"[{now}] 获取粉丝数失败")
            
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\n监控已停止")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            time.sleep(INTERVAL)

if __name__ == '__main__':
    monitor_fans()
