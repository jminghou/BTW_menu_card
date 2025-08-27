"""
Web版本的功能函數
將原有的tkinter相關功能改寫為Web版本
"""
import pandas as pd
import pymysql
import os
import tempfile
from datetime import datetime
from .config_sql import DB_CONFIG

def download_no_english_menus_web():
    """
    Web版本：下載資料庫中所有沒有英文的菜單資料
    返回檔案路徑而不是使用tkinter對話框
    """
    try:
        # 連接到MySQL資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 取得當前日期時間作為檔名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"menu_no_english_{current_time}.csv"
        
        # 使用臨時目錄
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
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
            return None  # 沒有資料
        
        # 轉換為DataFrame
        columns = ["序號", "餐廳編號", "餐廳名稱", "據點", "餐點編號", "菜牌編號", 
                  "餐點名稱", "英文名稱", "建檔日期", "資料表"]
        df = pd.DataFrame(all_results, columns=columns)
        
        # 按照菜牌編號排序
        df = df.sort_values(by='菜牌編號')
        
        # 儲存為CSV，設定編碼為UTF-8以支援中文
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path

    except Exception as e:
        print(f"下載無英文菜單資料時發生錯誤：{str(e)}")
        return None
    finally:
        # 關閉資料庫連接
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

def upload_english_names_web(file_path):
    """
    Web版本：上傳菜單英文名稱至資料庫功能
    """
    try:
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
            return False
        
        # 檢查必要欄位
        required_columns = ['菜牌編號', '英文名稱', '資料表']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"CSV檔案缺少以下欄位：{', '.join(missing_columns)}")
            return False
        
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
                print(f"已移除 {removed_count} 筆重複的菜牌編號記錄（保留有英文名稱的記錄）")
        
        # 資料庫連接
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 根據資料表分組
        table_groups = df.groupby('資料表')
        
        # 初始化計數器
        total_records = 0
        updated_records = 0
        error_records = 0
        
        # 處理每個資料表
        for table_name, group_df in table_groups:
            # 確認資料表名稱是否有效
            if table_name not in ['med_sun', 'med_tpr', 'med_tpx']:
                print(f"無效的資料表名稱：{table_name}")
                continue
            
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
                
            total_records += len(group_df)
        
        # 提交變更
        connection.commit()
        
        print(f"英文名稱上傳完成：總計 {total_records} 筆資料，成功更新 {updated_records} 筆")
        
        return True
        
    except Exception as e:
        print(f"上傳英文名稱時發生錯誤：{str(e)}")
        return False
    finally:
        # 關閉資料庫連接
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

def export_new_menus_web(date_range):
    """
    Web版本：導出指定日期區間內的新菜牌
    """
    try:
        from .mod4_new_menu_restaurant import MenuRestaurantExporter
        
        exporter = MenuRestaurantExporter()
        
        # 解析日期範圍
        if '-' in date_range:
            start_date, end_date = date_range.split('-')
        else:
            start_date = end_date = date_range
        
        # 生成檔案
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"new_menus_{date_range}_{current_time}.xlsx"
        
        # 使用臨時目錄
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # 調用導出功能（需要修改原函數以支援 Web 版本）
        result = exporter.export_new_menus_web(start_date, end_date, file_path)
        
        if result:
            return file_path
        else:
            return None
            
    except Exception as e:
        print(f"導出新菜牌時發生錯誤：{str(e)}")
        return None

def export_new_restaurants_web(date_range):
    """
    Web版本：導出指定日期區間內的新餐廳
    """
    try:
        from .mod4_new_menu_restaurant import MenuRestaurantExporter
        
        exporter = MenuRestaurantExporter()
        
        # 解析日期範圍
        if '-' in date_range:
            start_date, end_date = date_range.split('-')
        else:
            start_date = end_date = date_range
        
        # 生成檔案
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"new_restaurants_{date_range}_{current_time}.xlsx"
        
        # 使用臨時目錄
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # 調用導出功能（需要修改原函數以支援 Web 版本）
        result = exporter.export_new_restaurants_web(start_date, end_date, file_path)
        
        if result:
            return file_path
        else:
            return None
            
    except Exception as e:
        print(f"導出新餐廳時發生錯誤：{str(e)}")
        return None

def convert_csv_to_unicode_txt_web(file_paths):
    """
    Web版本：轉換CSV到TXT功能
    """
    try:
        from .mod2_utf8 import convert_csv_to_unicode_txt as original_convert
        
        result_files = []
        temp_dir = tempfile.gettempdir()
        
        for file_path in file_paths:
            # 讀取原始檔案
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            # 生成新檔案名
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{name}_{current_time}_BOM.txt"
            new_file_path = os.path.join(temp_dir, new_filename)
            
            # 讀取CSV並轉換
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                
                # 寫入帶BOM的UTF-8檔案
                with open(new_file_path, 'w', encoding='utf-8-sig') as outfile:
                    outfile.write(content)
                
                result_files.append({
                    'original': filename,
                    'converted': new_filename,
                    'path': new_file_path
                })
                
            except Exception as e:
                print(f"轉換檔案 {filename} 時發生錯誤：{str(e)}")
                continue
        
        return result_files
        
    except Exception as e:
        print(f"轉換CSV到TXT時發生錯誤：{str(e)}")
        return []

def download_all_web():
    """
    Web版本：下載所有菜牌資料
    """
    try:
        from .mod_sql_function import DatabaseFunction
        
        db_function = DatabaseFunction()
        
        # 生成檔案
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_menu_data_{current_time}.xlsx"
        
        # 使用臨時目錄
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # 調用下載功能（需要修改原函數以支援 Web 版本）
        result = db_function.download_all_web(file_path)
        
        if result:
            return file_path
        else:
            return None
            
    except Exception as e:
        print(f"下載所有菜牌資料時發生錯誤：{str(e)}")
        return None
    finally:
        if 'db_function' in locals():
            db_function.db.close_connection()
