import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import csv
from datetime import datetime
from .mod_sql import DatabaseUploader

def show_missing_codes(missing_codes):
    """
    顯示找不到的編號，並提供複製功能
    """
    # 創建新視窗
    window = tk.Toplevel()
    window.title("找不到的菜牌編號")
    window.geometry("400x300")

    # 創建框架
    frame = ttk.Frame(window, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    # 添加標籤
    label = ttk.Label(frame, text=f"以下 {len(missing_codes)} 個菜牌編號在資料庫中找不到：")
    label.pack(pady=(0, 10))

    # 創建文字區域
    text_area = tk.Text(frame, wrap=tk.WORD)
    text_area.pack(fill=tk.BOTH, expand=True)

    # 添加捲軸
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.configure(yscrollcommand=scrollbar.set)

    # 插入找不到的編號
    for code in sorted(missing_codes):
        text_area.insert(tk.END, f"{code}\n")

    # 創建複製按鈕
    def copy_to_clipboard():
        window.clipboard_clear()
        window.clipboard_append(text_area.get("1.0", tk.END))
        messagebox.showinfo("成功", "已複製到剪貼簿")

    copy_button = ttk.Button(frame, text="複製全部", command=copy_to_clipboard)
    copy_button.pack(pady=10)

def search_menu_codes(menu_codes):
    """
    搜尋菜牌編號並匯出結果
    """
    try:
        if not menu_codes:
            messagebox.showwarning("警告", "請輸入菜牌編號")
            return
            
        # 建立資料庫連接並搜尋
        uploader = DatabaseUploader()
        results = uploader.search_menu_codes(menu_codes)
        
        # 檢查哪些編號沒有找到
        found_codes = {row[5] for row in results}  # 現在菜牌編號是第6個欄位，因為第1個欄位是表名
        missing_codes = set(menu_codes) - found_codes
        
        if missing_codes:
            # 顯示找不到的編號
            show_missing_codes(missing_codes)
            
            if not results:  # 如果完全沒有找到任何資料
                return
            
            # 詢問是否要繼續匯出找到的資料
            if not messagebox.askyesno("確認", "是否要匯出已找到的資料？"):
                return
            
        # 產生檔案名稱（包含時間戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"menu_search_{timestamp}.csv"
        
        # 讓使用者選擇儲存位置
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        # 寫入CSV檔案
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 寫入標題，加入表名欄位
            headers = ["資料表", "序號", "餐廳編號", "餐廳名稱", "餐點編號", "菜牌編號", "餐點名稱", "英文名稱", "建檔日期"]
            writer.writerow(headers)
            # 寫入資料
            for row in results:
                writer.writerow(row)
                
        messagebox.showinfo("成功", f"資料已成功匯出至：\n{file_path}")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"搜尋過程中發生錯誤：\n{str(e)}") 