import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import os
from number import generate_menu_code
from pypinyin import lazy_pinyin
import re
from up_sql import DatabaseUploader

def convert_to_code(name):
    # 移除所有符號和空格，只保留字母和數字
    name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)
    
    # 檢查是否包含中文字符
    if any('\u4e00' <= char <= '\u9fff' for char in name):
        # 轉換中文為拼音，並取得首字母
        pinyin = ''.join([word[0] for word in lazy_pinyin(name)])
    else:
        # 如果是英文，移除所有空格
        pinyin = re.sub(r'\s+', '', name)
    
    # 轉換為大寫並取前5個字符
    return pinyin.upper()[:5]

def process_menu_codes():
    try:
        # 檢查input/build目錄是否存在
        input_dir = "input/build"
        if not os.path.exists(input_dir):
            messagebox.showerror("錯誤", "找不到input/build目錄")
            return

        # 獲取目錄中的所有Excel檔案
        excel_files = [f for f in os.listdir(input_dir) if f.endswith(('.xlsx', '.xls'))]
        
        if not excel_files:
            messagebox.showerror("錯誤", "在input/build目錄中找不到Excel檔案")
            return

        for excel_file in excel_files:
            file_path = os.path.join(input_dir, excel_file)
            
            try:
                # 讀取Excel檔案
                df = pd.read_excel(file_path)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法讀取檔案 {excel_file}：{str(e)}")
                continue

            # 尋找必要的欄位
            menu_name_col = None
            restaurant_col = None
            for col in df.columns:
                if "餐點名稱" in col:
                    menu_name_col = col
                if "餐廳" in col:
                    restaurant_col = col
            
            if menu_name_col is None:
                messagebox.showerror("錯誤", f"在{excel_file}中找不到'餐點名稱'欄位")
                continue
                
            if restaurant_col is None:
                messagebox.showerror("錯誤", f"在{excel_file}中找不到'餐廳'欄位")
                continue

            # 生成餐點編號
            df["餐點編號"] = df[menu_name_col].astype(str).apply(generate_menu_code)
            
            # 生成餐廳編號
            df["餐廳編號"] = df[restaurant_col].astype(str).apply(convert_to_code)
            
            # 組合完整編號
            df["菜牌編號"] = df["餐廳編號"] + "-" + df["餐點編號"]
            
            # 生成新檔名
            file_name = os.path.splitext(excel_file)[0]
            new_file_path = os.path.join(input_dir, f"{file_name}_with_codes.xlsx")
            
            # 儲存新檔案
            df.to_excel(new_file_path, index=False)
        
        messagebox.showinfo("成功", "已完成所有Excel檔案的處理")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"處理過程中發生錯誤：{str(e)}")

# 創建主視窗
root = tk.Tk()
root.title("菜牌管理程式")
root.geometry("300x300")  # 調整視窗大小以容納新按鈕

# 創建主框架
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(expand=True, fill='both')

# 創建產生編號按鈕
btn_generate = tk.Button(main_frame, text="產生菜牌編號", command=process_menu_codes)
btn_generate.pack(pady=20)

def upload_to_database():
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if file_path:
        uploader = DatabaseUploader()
        uploader.upload_file(file_path)

# 創建上傳資料庫按鈕
btn_upload = tk.Button(main_frame, text="上傳到資料庫", command=upload_to_database)
btn_upload.pack(pady=20)

# 啟動主循環
root.mainloop()
