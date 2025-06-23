import pandas as pd
import pymysql
from tkinter import messagebox, filedialog
from datetime import datetime
import os
from .config_sql import DB_CONFIG

def upload_english_names():
    """
    上傳菜單英文名稱至資料庫功能
    1. 讓使用者選擇CSV檔案
    2. 根據據點分類資料至對應資料表
    3. 更新對應菜牌編號的英文名稱
    4. 處理重複的菜牌編號（保留有英文名稱的記錄）
    """
    try:
        # 讓使用者選擇檔案
        file_path = filedialog.askopenfilename(
            title="選擇包含英文名稱的CSV檔案",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="menu_20250421_translated.csv" if os.path.exists("menu_20250421_translated.csv") else None
        )
        
        if not file_path:
            return
        
        # 嘗試不同的編碼讀取CSV檔案
        encodings = ['utf-8-sig', 'utf-8', 'big5', 'cp950', 'gbk']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"嘗試使用 {encoding} 編碼讀取失敗: {str(e)}")
        
        if df is None:
            messagebox.showerror("錯誤", "無法讀取CSV檔案，請確認檔案格式和編碼")
            return
        
        # 檢查必要欄位
        required_columns = ['菜牌編號', '英文名稱', '資料表']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            messagebox.showerror("錯誤", f"CSV檔案缺少以下欄位：\n{', '.join(missing_columns)}")
            return
        
        # 處理重複的菜牌編號（保留有英文名稱的記錄）
        # 將空白字符串和NaN都視為空值
        df['英文名稱'] = df['英文名稱'].fillna('').str.strip()
        
        # 找出重複的菜牌編號
        duplicates = df[df.duplicated(subset=['菜牌編號', '資料表'], keep=False)]
        if not duplicates.empty:
            # 將重複記錄按 菜牌編號和資料表 分組
            grouped = df.groupby(['菜牌編號', '資料表'])
            
            # 新的DataFrame，用於存放處理後的資料
            new_df_rows = []
            removed_count = 0
            
            for (menu_code, table_name), group in grouped:
                if len(group) > 1:
                    # 有重複的菜牌編號
                    # 按英文名稱是否為空來排序，非空的排在前面
                    sorted_group = group.sort_values(by='英文名稱', key=lambda x: x.str.len() > 0, ascending=False)
                    # 只保留第一筆記錄（有英文名稱的）
                    new_df_rows.append(sorted_group.iloc[0])
                    removed_count += len(group) - 1
                else:
                    # 沒有重複的菜牌編號，直接保留
                    new_df_rows.append(group.iloc[0])
            
            # 創建新的DataFrame
            df = pd.DataFrame(new_df_rows)
            
            if removed_count > 0:
                messagebox.showinfo("資訊", f"已移除 {removed_count} 筆重複的菜牌編號記錄（保留有英文名稱的記錄）")
        
        # 資料庫連接
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 根據資料表分組
        table_groups = df.groupby('資料表')
        
        # 初始化計數器
        total_records = 0
        updated_records = 0
        error_records = 0
        
        # 統計各表格的資料數量
        table_counts = {}
        table_updated = {}
        
        # 處理每個資料表
        for table_name, group_df in table_groups:
            # 確認資料表名稱是否有效
            if table_name not in ['med_sun', 'med_tpr', 'med_tpx']:
                messagebox.showerror("錯誤", f"無效的資料表名稱：{table_name}")
                continue
                
            # 記錄資料表的記錄數
            table_counts[table_name] = len(group_df)
            table_updated[table_name] = 0
            
            # 更新該資料表中的英文名稱
            for _, row in group_df.iterrows():
                menu_code = row['菜牌編號']
                english_name = row['英文名稱']
                
                # 如果英文名稱為空，則跳過
                if not english_name:
                    print(f"警告：菜牌編號 {menu_code} 的英文名稱為空")
                    continue
                
                # 檢查菜牌編號是否存在
                check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE 菜牌編號 = %s"
                cursor.execute(check_sql, (menu_code,))
                if cursor.fetchone()[0] == 0:
                    print(f"警告：資料表 {table_name} 中找不到菜牌編號 {menu_code}")
                    error_records += 1
                    continue
                
                # 更新英文名稱
                update_sql = f"UPDATE {table_name} SET 英文名稱 = %s WHERE 菜牌編號 = %s"
                cursor.execute(update_sql, (english_name, menu_code))
                updated_records += cursor.rowcount
                table_updated[table_name] += cursor.rowcount
                
            total_records += len(group_df)
        
        # 提交變更
        connection.commit()
        
        # 創建結果訊息
        result_message = "英文名稱上傳完成：\n\n"
        
        # 添加各表格的統計信息
        for table in sorted(table_counts.keys()):
            result_message += f"{table}: {table_counts[table]} 筆資料, 成功更新 {table_updated[table]} 筆\n"
        
        # 添加總計信息
        result_message += f"\n總計：{total_records} 筆資料\n"
        result_message += f"成功更新：{updated_records} 筆\n"
        if error_records > 0:
            result_message += f"錯誤記錄：{error_records} 筆\n"
        
        # 顯示結果
        messagebox.showinfo("上傳結果", result_message)
        
    except Exception as e:
        messagebox.showerror("錯誤", f"上傳英文名稱時發生錯誤：\n{str(e)}")
        print(f"詳細錯誤：{str(e)}")
    finally:
        # 關閉資料庫連接
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    # 用於直接測試此模組
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # 隱藏主窗口
    upload_english_names()
    root.destroy()
