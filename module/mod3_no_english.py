import pandas as pd
import pymysql
from tkinter import messagebox, filedialog
from datetime import datetime
from .config_sql import DB_CONFIG

def download_no_english_menus():
    """
    下載資料庫中所有沒有英文的菜單資料
    包括med_sun, med_tpr, med_tpx三個資料表的資料
    """
    try:
        # 連接到MySQL資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 取得當前日期時間作為檔名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"menu_no_english_{current_time}.csv"
        
        # 讓使用者選擇儲存位置
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # 需要查詢的資料表
        tables = ['med_sun', 'med_tpr', 'med_tpx']
        
        all_results = []
        table_raw_counts = {}  # 紀錄每個表格的原始資料數量
        table_unique_counts = {}  # 紀錄每個表格去重後的資料數量
        
        # 從每個資料表中獲取沒有英文名稱的菜單資料
        for table in tables:
            # 檢查表格是否存在
            check_table_sql = f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table}'
            """
            cursor.execute(check_table_sql)
            if cursor.fetchone()[0] == 0:
                continue  # 表格不存在，跳過
            
            # 首先獲取原始資料數量
            raw_count_query = f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE 英文名稱 IS NULL OR 英文名稱 = ''
            """
            cursor.execute(raw_count_query)
            table_raw_counts[table] = cursor.fetchone()[0]
            
            # 從該表格中查詢沒有英文名稱的資料
            query = f"""
            SELECT 序號, 餐廳編號, 餐廳名稱, 據點, 餐點編號, 菜牌編號, 餐點名稱, 英文名稱, 建檔日期
            FROM {table}
            WHERE 英文名稱 IS NULL OR 英文名稱 = ''
            ORDER BY 菜牌編號
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 將結果轉換為DataFrame進行據點內去重
            columns = ["序號", "餐廳編號", "餐廳名稱", "據點", "餐點編號", "菜牌編號", 
                     "餐點名稱", "英文名稱", "建檔日期"]
            table_df = pd.DataFrame(results, columns=columns)
            
            # 記錄去重前的資料筆數
            before_dedup = len(table_df)
            
            # 按據點和餐點編號去重，保留第一筆出現的資料
            table_df = table_df.drop_duplicates(subset=['據點', '餐點編號'], keep='first')
            
            # 記錄去重後的資料筆數
            after_dedup = len(table_df)
            table_unique_counts[table] = after_dedup
            
            # 將表格名稱添加到每一行結果中
            for _, row in table_df.iterrows():
                # 將Series轉換為列表
                row_list = row.tolist()
                # 添加表格名稱
                row_list.append(table)
                # 將列表轉換為元組，並添加到結果列表中
                all_results.append(tuple(row_list))
        
        if not all_results:
            messagebox.showinfo("提示", "資料庫中沒有找到無英文名稱的菜單資料")
            return
        
        # 轉換為DataFrame
        columns = ["序號", "餐廳編號", "餐廳名稱", "據點", "餐點編號", "菜牌編號", 
                  "餐點名稱", "英文名稱", "建檔日期", "資料表"]
        df = pd.DataFrame(all_results, columns=columns)
        
        # 按照菜牌編號排序
        df = df.sort_values(by='菜牌編號')
        
        # 儲存為CSV，設定編碼為UTF-8以支援中文
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        # 創建每個表格資料筆數的訊息
        table_count_msg = "\n".join([
            f"{table}: {raw} 筆 (原始) → {unique} 筆 (據點內去重) [減少 {raw-unique} 筆]" 
            for table, raw, unique in zip(
                table_raw_counts.keys(), 
                table_raw_counts.values(), 
                table_unique_counts.values()
            )
        ])
        
        messagebox.showinfo("成功", 
                           f"無英文菜單資料已成功下載至：\n{file_path}\n\n"
                           f"各表格資料筆數：\n{table_count_msg}\n\n"
                           f"總計：{len(df)} 筆資料\n"
                           f"每個據點內的重複餐點編號已去除")

    except Exception as e:
        messagebox.showerror("錯誤", f"下載無英文菜單資料時發生錯誤：\n{str(e)}")
    finally:
        # 關閉資料庫連接
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()
