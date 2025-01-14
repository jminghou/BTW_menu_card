import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
from .mod_number import generate_menu_code, convert_to_code

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
        
        # 尋找並刪除"售價"和"餐點編號"
        columns_to_drop = []
        price_columns = [col for col in df.columns if "售價" in col]
        menu_number_columns = [col for col in df.columns if "餐點編號" in col]
        
        columns_to_drop.extend(price_columns)
        columns_to_drop.extend(menu_number_columns)
        
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        
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
        location_col = location_columns[0] if location_columns else None
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
                df[menu_col] = df[menu_col].str.strip()
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
            empty_rows = df[branch_columns + menu_columns].apply(
                lambda x: x.isna() | (x == ''), axis=1
            ).all(axis=1)
            df = df[~empty_rows]

        # 處理所有欄位中的"咔"字
        for column in df.columns:
            try:
                if df[column].dtype == 'object':
                    df[column] = df[column].str.replace('咔', '卡', regex=False)
            except:
                continue

        # 獲取原始檔名和路徑
        file_dir = os.path.dirname(file_path)
        original_name = os.path.splitext(os.path.basename(file_path))[0]

        # 創建一個新的 DataFrame，不包含餐點名稱欄位
        output_df = df.copy()
        menu_name_columns = [col for col in output_df.columns if "餐點名稱" in col]
        if menu_name_columns:
            output_df = output_df.drop(columns=menu_name_columns)
            
        # 找出日期欄位
        date_columns = [col for col in output_df.columns if "日期" in col]
        if date_columns and "餐廳名稱" in output_df.columns:
            # 使用第一個找到的日期欄位
            date_col = date_columns[0]
            # 根據日期和餐廳名稱去重複，保留第一筆記錄
            output_df = output_df.drop_duplicates(subset=[date_col, "餐廳名稱"], keep='first')
            print(f"已根據{date_col}和餐廳名稱去除重複記錄")

        if location_col:
            # 定義三個據點名稱
            locations = ["聯發科瑞光", "聯發科行善", "聯發太陽廣場"]
            
            # 儲存完整檔案
            complete_file_path = os.path.join(file_dir, f"{original_name}_完整.xlsx")
            output_df.to_excel(complete_file_path, index=False)
            
            # 為每個據點創建獨立的DataFrame並儲存
            for location in locations:
                location_df = output_df[output_df[location_col] == location].copy()
                
                if not location_df.empty:
                    new_file_path = os.path.join(file_dir, f"{original_name}_{location}.xlsx")
                    location_df.to_excel(new_file_path, index=False)
            
            messagebox.showinfo("成功", f"檔案已依據點分類並存在：\n{file_dir}\n包含完整檔案及各據點檔案")
        else:
            new_file_path = os.path.join(file_dir, f"{original_name}_cleaned.xlsx")
            output_df.to_excel(new_file_path, index=False)
            messagebox.showinfo("成功", f"文件已清理完成並保存為：\n{new_file_path}")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"處理過程中發生錯誤：{str(e)}")