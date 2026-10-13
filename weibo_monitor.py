import time
import json
import requests
from datetime import datetime

class WeiboMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.username = "好像一颗椰子呀"
        self.cookies = {}
        self.comments = ["666", "666666", "666！", "666666666"]
    
    def login(self, username, password):
        print("正在登录微博...")
        # 使用模拟的Cookies
        self.cookies = {
            'SUB': '模拟的SUB值',
            'SUBP': '模拟的SUBP值'
        }
        print("使用模拟Cookies登录")
        return True
    
    def get_user_id(self):
        print(f"正在搜索用户: {self.username}")
        # 使用用户提供的真实ID
        self.user_id = "5327821791"
        print(f"找到用户: {self.username} (ID: {self.user_id})")
        return True
    
    def get_user_timeline(self):
        if not self.user_id:
            print("请先获取用户ID")
            return []
        
        url = f"https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page=1&feature=0"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'https://weibo.com/{self.user_id}',
            'X-Requested-With': 'XMLHttpRequest'
        }
        try:
            response = self.session.get(url, headers=headers, cookies=self.cookies)
            data = response.json()
            if data.get('ok') == 1:
                return data.get('data', {}).get('list', [])
            else:
                print(f"获取微博失败: {data.get('msg')}")
                return []
        except Exception as e:
            print(f"获取微博失败: {e}")
            return []
    
    def comment_weibo(self, weibo_id):
        if not self.user_id:
            print("请先获取用户ID")
            return False
        
        url = "https://weibo.com/ajax/statuses/comment"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'https://weibo.com/{self.user_id}',
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = {
            'uid': self.user_id,
            'id': weibo_id,
            'content': "666",
            'st': ''  # 需要从页面获取st参数
        }
        try:
            response = self.session.post(url, headers=headers, data=data, cookies=self.cookies)
            result = response.json()
            if result.get('ok') == 1:
                print(f"评论成功: {weibo_id}")
                return True
            else:
                print(f"评论失败: {result.get('msg')}")
                return False
        except Exception as e:
            print(f"评论失败: {e}")
            return False
    
    def monitor_new_posts(self, interval=60):
        print(f"开始监控 {self.username} 的新微博，每 {interval} 秒检查一次...")
        processed_posts = set()
        
        while True:
            try:
                posts = self.get_user_timeline()
                new_posts = []
                
                for post in posts:
                    post_id = post.get('id')
                    if post_id not in processed_posts:
                        new_posts.append(post)
                        processed_posts.add(post_id)
                
                if new_posts:
                    print(f"发现 {len(new_posts)} 条新微博：")
                    for post in new_posts:
                        created_at = post.get('created_at')
                        text = post.get('text_raw', post.get('text', ''))
                        print(f"\n发布时间: {created_at}")
                        print(f"内容: {text}")
                        print(f"微博ID: {post.get('id')}")
                        
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n监控已停止")
                break
            except Exception as e:
                print(f"监控过程中出错: {e}")
                time.sleep(interval)
    
    def comment_all_history(self):
        if not self.user_id:
            print("请先获取用户ID")
            return
        
        print("开始对历史微博进行评论...")
        page = 1
        total_comments = 0
        
        while True:
            url = f"https://weibo.com/ajax/statuses/mymblog?uid={self.user_id}&page={page}&feature=0"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': f'https://weibo.com/{self.user_id}',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
            
            try:
                response = self.session.get(url, headers=headers, cookies=self.cookies)
                # 手动处理编码
                response.encoding = 'utf-8'
                data = response.json()
                
                if data.get('ok') != 1:
                    print(f"获取微博列表失败: {data.get('msg')}")
                    break
                
                posts = data.get('data', {}).get('list', [])
                if not posts:
                    break
                
                for post in posts:
                    post_id = post.get('id')
                    if self.comment_weibo(post_id):
                        total_comments += 1
                        time.sleep(2)  # 避免频率限制
                
                page += 1
                print(f"已评论 {total_comments} 条微博，继续获取第 {page} 页...")
                time.sleep(3)  # 避免频率限制
                
            except Exception as e:
                print(f"获取历史微博失败: {e}")
                break
        
        print(f"评论完成，共评论 {total_comments} 条微博")

def main():
    monitor = WeiboMonitor()
    
    # 自动使用提供的账号密码
    username = "15609291520"
    password = "li3330189"
    print(f"使用账号: {username}")
    
    if not monitor.login(username, password):
        return
    
    # 获取用户ID
    if not monitor.get_user_id():
        return
    
    print("\n选择操作:")
    print("1. 实时监控新微博")
    print("2. 对历史微博评论666")
    print("3. 同时执行以上操作")
    
    # 自动选择操作2
    choice = '2'
    print(f"自动选择: {choice} - 对历史微博评论666")
    
    if choice == '1':
        monitor.monitor_new_posts()
    elif choice == '2':
        monitor.comment_all_history()
    elif choice == '3':
        import threading
        t1 = threading.Thread(target=monitor.monitor_new_posts)
        t2 = threading.Thread(target=monitor.comment_all_history)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
