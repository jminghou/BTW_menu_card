import pymysql
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

class DatabaseExporter:
    def __init__(self):
        self.connect_database()

    def connect_database(self):
        try:
            self.connection = pymysql.connect(
                host='localhost',
                user='root',
                password='12345678',
                database='db_mediatek_menu',
                charset='utf8mb4'
            )
            self.cursor = self.connection.cursor()
        except Exception as e:
            messagebox.showerror("錯誤", f"資料庫連接失敗：\n{str(e)}")
            raise e

    def close_connection(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
        except Exception as e:
            print(f"關閉連接時發生錯誤：{str(e)}")

    def export_to_txt(self):
        try:
            # 取得當前日期時間作為檔名
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"menu_export_{current_time}.txt"
            
            # 開啟檔案選擇對話框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialfile=default_filename,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # 查詢資料
            query = """
            SELECT 序號, 餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 餐點名稱, 英文名稱
            FROM menu_items
            ORDER BY 序號
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # 寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                # 寫入標題列
                headers = ["序號", "餐廳編號", "餐廳名稱", "餐點編號", "菜牌編號", "餐點名稱", "英文名稱"]
                f.write('\t'.join(headers) + '\n')
                
                # 寫入資料列
                for row in results:
                    # 將所有欄位轉換為字串並去除空白
                    formatted_row = [str(item).strip() if item is not None else '' for item in row]
                    f.write('\t'.join(formatted_row) + '\n')
            
            messagebox.showinfo("成功", f"資料已成功匯出至：\n{file_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出過程中發生錯誤：\n{str(e)}")
            return False
        
    def __del__(self):
        self.close_connection()

def main():
    # 創建主視窗
    root = tk.Tk()
    root.title("菜單資料匯出程式")
    root.geometry("300x150")

    # 創建主框架
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(expand=True, fill='both')

    # 創建匯出按鈕
    exporter = DatabaseExporter()
    btn_export = tk.Button(
        main_frame, 
        text="匯出菜單資料", 
        command=exporter.export_to_txt,
        height=2
    )
    btn_export.pack(pady=20)

    # 啟動主循環
    root.mainloop()

if __name__ == "__main__":
    main() 