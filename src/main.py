import os
import sys

# 将 src 目录添加到 Python 路径
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dotenv import load_dotenv
from agents.main_controller import MainController


def main():
    """智能穿搭助手 CLI 入口"""
    load_dotenv()
    
    print("=" * 50)
    print("    智能穿搭助手 v1.0")
    print("=" * 50)
    print("欢迎使用智能穿搭助手！")
    print("我可以根据天气和您的衣橱为您推荐穿搭。")
    print("您可以说：")
    print("  - '今天天气怎么样'")
    print("  - '帮我看看穿什么'")
    print("  - '今天下午有个面试，穿什么合适'")
    print("  - '添加衣服'")
    print("  - '查看衣橱'")
    print("输入 '退出' 或 'quit' 结束对话")
    print("-" * 50)
    
    controller = MainController()
    chat_history = []
    
    while True:
        try:
            user_input = input("\n您：").strip()
            
            if user_input.lower() in ["退出", "quit", "exit"]:
                print("助手：再见！希望您今天有个好心情~")
                break
            
            if not user_input:
                print("助手：请输入您的问题或需求。")
                continue
            
            print("助手：思考中...")
            
            result = controller.invoke(user_input, chat_history)
            chat_history = result.get("chat_history", [])
            
            print(f"\n助手：{result.get('final_output', '暂无回复')}")
            
        except KeyboardInterrupt:
            print("\n助手：再见！")
            break
        except Exception as e:
            print(f"助手：抱歉，发生了错误：{str(e)}")


if __name__ == "__main__":
    main()
