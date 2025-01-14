import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
from delete.number import generate_menu_code
from pypinyin import lazy_pinyin
import re

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

def clean_excel_file():
    try:
        # 讓用戶選擇Excel文件
        file_path = filedialog.askopenfilename(
            title="選擇要清理的Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
            
        # 讀取Excel文件
        df = pd.read_excel(file_path)
        
        # 尋找並刪除"售價"
        price_columns = [col for col in df.columns if "售價" in col]
        if price_columns:
            df = df.drop(columns=price_columns)
        
        # 處理日期欄位
        date_columns = [col for col in df.columns if "日期" in col]
        for date_col in date_columns:
            try:
                # 將日期轉換為月/日格式
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%m/%d')
            except:
                continue
        
        # 處理據點欄位
        location_columns = [col for col in df.columns if "據點" in col]
        for loc_col in location_columns:
            try:
                # 移除 "-內部" 字串
                df[loc_col] = df[loc_col].str.replace('-內部', '', regex=False)
            except:
                continue
        
        # 處理分店欄位
        branch_columns = []
        for col in df.columns:
            if any(keyword in col for keyword in ["分店", "店家", "餐廳", "分　店", "店　家", "餐　廳"]):
                branch_columns.append(col)

        if not branch_columns:
            print("警告：找不到分店相關欄位")
            print("所有欄位名稱：", list(df.columns))
            messagebox.showwarning("警告", "找不到分店相關欄位，請確Excel檔案格式是否正確")
            return

        # 儲存原始欄位名稱
        original_column_name = branch_columns[0]
        print(f"找到分店欄位：{original_column_name}")

        try:
            # 確保資料為字串類型
            df[original_column_name] = df[original_column_name].astype(str)
            # 移除 "-" 及其後的所有文字
            df[original_column_name] = df[original_column_name].str.split('-').str[0]
            # 將分店欄位改名為"餐廳名稱"
            df = df.rename(columns={original_column_name: "餐廳名稱"})
            print(f"已將 '{original_column_name}' 改名為 '餐廳名稱'")
            
            # 更新 branch_columns 列表
            branch_columns = ["餐廳名稱"]
            
        except Exception as e:
            print(f"處理欄位時發生錯誤: {str(e)}")
            return

        # 處理餐點名稱欄位
        menu_columns = [col for col in df.columns if "餐點名稱" in col]
        for menu_col in menu_columns:
            try:
                # 移除 "+" 和 "＋" 符號
                df[menu_col] = df[menu_col].str.replace('+', '', regex=False)
                df[menu_col] = df[menu_col].str.replace('＋', '', regex=False)
                # 移除 "(中)" 和 "(牛)"
                df[menu_col] = df[menu_col].str.replace('(中)', '', regex=False)
                df[menu_col] = df[menu_col].str.replace('(牛)', '', regex=False)
                
                # 檢查餐點名稱是否為空白或 NaN
                # 將空字串、純空格、NaN 都視為空值
                df[menu_col] = df[menu_col].str.strip()  # 移除前後空格
                empty_menu = df[menu_col].isna() | (df[menu_col] == '')
                
                # 刪除餐點名稱為空的列
                if empty_menu.any():
                    print(f"發現 {empty_menu.sum()} 筆空白餐點名稱記錄，已刪除")
                    df = df[~empty_menu]
                    
            except Exception as e:
                print(f"處理餐點名稱時發生錯誤: {str(e)}")
                continue

        # 刪除分店和餐點名稱都是空白的列
        if branch_columns and menu_columns:
            # 檢查這些欄位是否都是空白（NaN或空字串）
            empty_rows = df[branch_columns + menu_columns].apply(
                lambda x: x.isna() | (x == ''), axis=1
            ).all(axis=1)
            # 保留非空白的列
            df = df[~empty_rows]

        # 處理所有欄位中的"咔"字
        for column in df.columns:
            try:
                if df[column].dtype == 'object':
                    df[column] = df[column].str.replace('咔', '卡', regex=False)
            except:
                continue

        # 在最前面插入三個新欄位
        df.insert(0, "餐廳編號", "")
        df.insert(1, "餐點編號", "")
        df.insert(2, "菜牌編號", "")

        # 找到據點欄位
        location_col = None
        for col in df.columns:
            if "據點" in col:
                location_col = col
                break

        # 獲取原始檔名（不含副檔名）和路徑
        file_dir = os.path.dirname(file_path)
        original_name = os.path.splitext(os.path.basename(file_path))[0]

        if location_col:
            # 定義三個據點名稱
            locations = ["聯發科瑞光", "聯發科行善", "聯發太陽廣場"]
            
            # 先儲存完整的檔案
            complete_file_path = os.path.join(file_dir, f"{original_name}_完整.xlsx")
            df.to_excel(complete_file_path, index=False)
            
            # 為每個據點創建獨立的DataFrame並儲存
            for location in locations:
                # 篩選特定據點的資料
                location_df = df[df[location_col] == location].copy()
                
                if not location_df.empty:
                    # 生成新檔名
                    new_file_path = os.path.join(file_dir, f"{original_name}_{location}.xlsx")
                    
                    # 儲存檔案
                    location_df.to_excel(new_file_path, index=False)
            
            messagebox.showinfo("成功", f"檔案已依據點分類並存在：\n{file_dir}\n包含完整檔案及各據點檔案")
        else:
            # 如果找不到據點欄位，就只儲存一個清理後的檔案
            new_file_path = os.path.join(file_dir, f"{original_name}_cleaned.xlsx")
            df.to_excel(new_file_path, index=False)
            messagebox.showinfo("成功", f"文件已清理完成並保存為：\n{new_file_path}")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"處理過程中發生錯誤：{str(e)}")
