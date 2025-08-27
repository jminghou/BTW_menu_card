"""
菜牌管理系統 - Flask Web 版本啟動點
"""
from app import app
import webbrowser
import threading
import time

def open_browser():
    """5秒後自動開啟瀏覽器"""
    time.sleep(5)
    webbrowser.open('http://localhost:5000')

def main():
    """啟動 Flask 應用程式"""
    print("=" * 50)
    print("🍴 菜牌管理系統 - Web版本")
    print("=" * 50)
    print("🌐 應用程式正在啟動...")
    print("📱 請在瀏覽器中訪問：http://localhost:5000")
    print("🔧 調試模式：已啟用")
    print("=" * 50)
    
    # 在新線程中啟動瀏覽器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 啟動 Flask 應用程式
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"❌ 啟動失敗：{str(e)}")
        print("請檢查：")
        print("1. 端口 5000 是否被其他程式占用")
        print("2. 資料庫連接是否正常")
        print("3. 依賴套件是否已安裝：pip install -r requirements.txt")

if __name__ == "__main__":
    main()
