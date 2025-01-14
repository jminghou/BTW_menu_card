import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import os
from module.mod_number import process_menu_codes
from module.mod_sql import DatabaseUploader
from module.mod_difference import MenuDifferenceCalculator
from module.mod_clean import clean_excel_file
import csv
from tkinter import ttk
from datetime import datetime
from module.mod_search import search_menu_codes
from module.mod_sql_function import DatabaseFunction
from module.mod_calendar import clean_excel_file

def process_menu_codes_ui():
    try:
        # 讓用戶選擇Excel文件
        file_path = filedialog.askopenfilename(
            title="選擇要產生編號的Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
            
        new_file_path, error = process_menu_codes(file_path)
        
        if error:
            messagebox.showerror("錯誤", error)
            return
            
        messagebox.showinfo("成功", f"已完成編號產生，檔案已儲存為：\n{new_file_path}")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"處理過程中發生錯誤：{str(e)}")

def upload_to_database():
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if file_path:
        uploader = DatabaseUploader()
        uploader.upload_file(file_path)

def filter_menu_codes():
    calculator = MenuDifferenceCalculator()
    calculator.calculate_difference()

def search_menu_code():
    # 獲取文本框中的所有菜牌編號
    menu_codes = entry_menu_code.get('1.0', tk.END).strip().split('\n')
    menu_codes = [code.strip() for code in menu_codes if code.strip()]
    search_menu_codes(menu_codes)

def check_duplicates():
    db_function = DatabaseFunction()
    db_function.check_duplicates()

def remove_duplicates():
    db_function = DatabaseFunction()
    db_function.remove_duplicates()

def download_all():
    db_function = DatabaseFunction()
    db_function.download_all()

def main():
    # 創建主視窗
    root = tk.Tk()
    root.title("菜牌管理程式")
    root.geometry("400x600")  # 調整視窗大小

    # 創建主框架
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(expand=True, fill='both')

    # 創建功能按鈕框架
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill='x', pady=20)

    # 設定按鈕共同樣式
    button_width = 12
    button_height = 2

    # 創建第一排按鈕（三個並排）
    btn_clean = tk.Button(
        button_frame,
        text="資料清洗",
        command=clean_excel_file,
        width=button_width,
        height=button_height
    )
    btn_clean.pack(side='left', expand=True, padx=5)

    btn_generate = tk.Button(
        button_frame,
        text="菜牌編號產生",
        command=process_menu_codes_ui,
        width=button_width,
        height=button_height
    )
    btn_generate.pack(side='left', expand=True, padx=5)

    btn_upload = tk.Button(
        button_frame,
        text="上傳資料庫",
        command=upload_to_database,
        width=button_width,
        height=button_height
    )
    btn_upload.pack(side='left', expand=True, padx=5)

    # 在第一排按鈕之後，添加第二排按鈕
    button_frame2 = tk.Frame(main_frame)
    button_frame2.pack(fill='x', pady=20)

    # 創建第二排按鈕（四個並排）
    btn_check = tk.Button(
        button_frame2,
        text="檢查重複",
        command=check_duplicates,
        width=button_width,
        height=button_height
    )
    btn_check.pack(side='left', expand=True, padx=5)

    btn_remove = tk.Button(
        button_frame2,
        text="刪除重複",
        command=remove_duplicates,
        width=button_width,
        height=button_height
    )
    btn_remove.pack(side='left', expand=True, padx=5)

    btn_download = tk.Button(
        button_frame2,
        text="下載菜牌",
        command=download_all,
        width=button_width,
        height=button_height
    )
    btn_download.pack(side='left', expand=True, padx=5)

    btn_calendar = tk.Button(
        button_frame2,
        text="輸出美食報報",
        command=clean_excel_file,
        width=button_width,
        height=button_height
    )
    btn_calendar.pack(side='left', expand=True, padx=5)

    # 創建篩選按鈕
    btn_filter = tk.Button(
        main_frame,
        text="篩選菜牌",
        command=filter_menu_codes,
        height=2
    )
    btn_filter.pack(pady=20, fill='x')

    # 創建搜尋框架（移到底部）
    search_frame = ttk.LabelFrame(main_frame, text="搜尋菜牌 (可複製多個編號，每行一個)", padding=(10, 5))
    search_frame.pack(fill='both', expand=True, pady=(0, 10))

    # 將 Entry 改為 Text，並設定更大的高度
    global entry_menu_code
    entry_menu_code = tk.Text(search_frame, height=15, width=20)
    entry_menu_code.pack(side='left', padx=(0, 5), fill='both', expand=True)
    
    # 添加垂直滾動條
    scrollbar = ttk.Scrollbar(search_frame, orient="vertical", command=entry_menu_code.yview)
    scrollbar.pack(side='right', fill='y')
    entry_menu_code.configure(yscrollcommand=scrollbar.set)
    
    # 搜尋按鈕
    btn_search = ttk.Button(
        main_frame,
        text="搜尋",
        command=search_menu_code
    )
    btn_search.pack(fill='x')  # 調整按鈕位置

    # 啟動主循環
    root.mainloop()

if __name__ == "__main__":
    main()
