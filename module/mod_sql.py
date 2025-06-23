import pandas as pd
from datetime import datetime
from tkinter import messagebox
import pymysql
import os
from module.config_sql import DB_CONFIG

class DatabaseUploader:
    def __init__(self):
        self.connect_database()

    def connect_database(self):
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
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

    def search_menu_codes(self, menu_codes):
        """
        搜尋菜牌編號並返回結果
        """
        try:
            if not hasattr(self, 'connection') or self.connection.open == False:
                self.connect_database()
                
            # 需要搜尋的表格清單
            tables = ['med_tpr', 'med_tpx', 'med_sun', 'menu_items']
            
            all_results = []
            
            # 從每個表格中搜尋菜牌編號
            for table in tables:
                # 檢查表格是否存在
                check_table_sql = f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table}'
                """
                self.cursor.execute(check_table_sql)
                if self.cursor.fetchone()[0] == 0:
                    continue  # 表格不存在，跳過
                
                # 從該表格中搜尋菜牌編號
                query = f"""
                SELECT 序號, 餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 餐點名稱, 英文名稱, 據點, 建檔日期
                FROM {table}
                WHERE 菜牌編號 IN (%s)
                """
                placeholders = ','.join(['%s'] * len(menu_codes))
                if not placeholders:
                    continue  # 沒有要搜尋的編號，跳過
                
                query = query % placeholders
                
                self.cursor.execute(query, menu_codes)
                results = self.cursor.fetchall()
                
                # 將表格名稱添加到每一行結果中
                table_results = [(table,) + row for row in results]
                all_results.extend(table_results)
            
            return all_results
            
        except Exception as e:
            messagebox.showerror("錯誤", f"搜尋菜牌編號時發生錯誤：\n{str(e)}")
            print("詳細錯誤：", str(e))
            return []

    def upload_file(self, file_path):
        try:
            # 確保資料庫連接是開啟的
            if not hasattr(self, 'connection') or self.connection.open == False:
                self.connect_database()

            # 讀取Excel檔案
            df = pd.read_excel(file_path)
            
            # 檢查必要欄位
            required_columns = ['餐廳編號', '餐廳名稱', '餐點編號', '菜牌編號', '餐點名稱']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("錯誤", f"Excel檔案缺少以下欄位：\n{', '.join(missing_columns)}")
                return False

            # 添加建檔日期
            df['建檔日期'] = datetime.now()

            # 確保英文名稱欄位存在
            if '英文名稱' not in df.columns:
                df['英文名稱'] = ''

            # 根據據點將數據分組處理
            location_map = {
                '聯發科瑞光': 'med_tpr',
                '聯發科行善': 'med_tpx',
                '聯發太陽廣場': 'med_sun'
            }
            
            # 創建所有需要的表（如果不存在）
            base_table_sql = """
            CREATE TABLE IF NOT EXISTS {table_name} (
                序號 INT AUTO_INCREMENT PRIMARY KEY,
                餐廳編號 VARCHAR(10) NOT NULL,
                餐廳名稱 VARCHAR(100) NOT NULL,
                餐點編號 VARCHAR(10) NOT NULL,
                菜牌編號 VARCHAR(20) NOT NULL,
                餐點名稱 VARCHAR(100) NOT NULL,
                英文名稱 VARCHAR(100),
                據點 VARCHAR(100) NOT NULL,
                建檔日期 DATETIME NOT NULL
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
            
            for table_name in location_map.values():
                create_table_sql = base_table_sql.format(table_name=table_name)
                self.cursor.execute(create_table_sql)
                
                # 检查表是否已存在"据点"字段，如果不存在则添加
                check_column_sql = f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}'
                AND column_name = '據點'
                """
                self.cursor.execute(check_column_sql)
                if self.cursor.fetchone()[0] == 0:
                    # 添加"据点"字段
                    alter_table_sql = f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN 據點 VARCHAR(100) NOT NULL DEFAULT ''
                    """
                    self.cursor.execute(alter_table_sql)
            
            # 同样为menu_items表检查并添加"据点"字段
            check_menu_items_sql = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'menu_items'
            """
            self.cursor.execute(check_menu_items_sql)
            if self.cursor.fetchone()[0] > 0:
                # 表已存在，检查是否有"据点"字段
                check_column_sql = """
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'menu_items'
                AND column_name = '據點'
                """
                self.cursor.execute(check_column_sql)
                if self.cursor.fetchone()[0] == 0:
                    # 添加"据点"字段
                    alter_table_sql = """
                    ALTER TABLE menu_items
                    ADD COLUMN 據點 VARCHAR(100) NOT NULL DEFAULT ''
                    """
                    self.cursor.execute(alter_table_sql)
            
            self.connection.commit()
            
            success_count = 0
            skipped_count = 0
            
            # 按據點處理數據
            # 確保據點欄位存在
            if '據點' not in df.columns:
                df['據點'] = ''
                # 根據餐廳名稱映射據點
                for restaurant_name in location_map.keys():
                    df.loc[df['餐廳名稱'] == restaurant_name, '據點'] = restaurant_name
            
            for location_name, table_name in location_map.items():
                # 篩選出特定據點的數據
                location_df = df[df['據點'] == location_name]
                
                # 如果據點欄位為空，嘗試用餐廳名稱匹配
                if location_df.empty:
                    location_df = df[df['餐廳名稱'] == location_name]
                    # 設置據點欄位
                    location_df.loc[:, '據點'] = location_name
                
                if location_df.empty:
                    continue
                
                # 檢查該表中現有的菜牌編號
                check_sql = f"SELECT 菜牌編號 FROM {table_name}"
                self.cursor.execute(check_sql)
                existing_codes = {row[0] for row in self.cursor.fetchall()}
                
                # 檢查新數據中的菜牌編號是否有重複
                new_codes = set(location_df['菜牌編號'].astype(str))
                duplicate_codes = new_codes.intersection(existing_codes)
                
                if duplicate_codes:
                    skipped_count += len(duplicate_codes)
                    # 從數據框中移除重複的記錄
                    location_df = location_df[~location_df['菜牌編號'].astype(str).isin(duplicate_codes)]
                
                if location_df.empty:
                    continue
                
                # 準備插入語句
                insert_sql = f"""
                INSERT INTO {table_name} 
                (餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 
                 餐點名稱, 英文名稱, 據點, 建檔日期)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 批次處理資料
                batch_size = 100
                for i in range(0, len(location_df), batch_size):
                    batch = location_df.iloc[i:i+batch_size]
                    values = []
                    for _, row in batch.iterrows():
                        # 处理英文名称，确保即使为NaN或None也能正确处理
                        eng_name = ''
                        if '英文名稱' in df.columns:
                            if pd.notna(row['英文名稱']):
                                eng_name = str(row['英文名稱']).strip()
                        
                        values.append((
                            str(row['餐廳編號']).strip(),
                            str(row['餐廳名稱']).strip(),
                            str(row['餐點編號']).strip(),
                            str(row['菜牌編號']).strip(),
                            str(row['餐點名稱']).strip(),
                            eng_name,
                            location_name,
                            row['建檔日期']
                        ))
                    
                    self.cursor.executemany(insert_sql, values)
                    success_count += len(batch)
                
                self.connection.commit()
            
            # 處理不屬於指定據點的資料
            other_df = df[~df['據點'].isin(location_map.keys())]
            
            if not other_df.empty:
                # 為其他據點創建默認表
                self.cursor.execute(base_table_sql.format(table_name='menu_items'))
                self.connection.commit()
                
                # 檢查默認表中現有的菜牌編號
                check_sql = "SELECT 菜牌編號 FROM menu_items"
                self.cursor.execute(check_sql)
                existing_codes = {row[0] for row in self.cursor.fetchall()}
                
                # 檢查新數據中的菜牌編號是否有重複
                new_codes = set(other_df['菜牌編號'].astype(str))
                duplicate_codes = new_codes.intersection(existing_codes)
                
                if duplicate_codes:
                    skipped_count += len(duplicate_codes)
                    # 從數據框中移除重複的記錄
                    other_df = other_df[~other_df['菜牌編號'].astype(str).isin(duplicate_codes)]
                
                if not other_df.empty:
                    # 準備插入語句
                    insert_sql = """
                    INSERT INTO menu_items 
                    (餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 
                     餐點名稱, 英文名稱, 據點, 建檔日期)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # 批次處理資料
                    batch_size = 100
                    for i in range(0, len(other_df), batch_size):
                        batch = other_df.iloc[i:i+batch_size]
                        values = []
                        for _, row in batch.iterrows():
                            # 处理英文名称，确保即使为NaN或None也能正确处理
                            eng_name = ''
                            if '英文名稱' in df.columns:
                                if pd.notna(row['英文名稱']):
                                    eng_name = str(row['英文名稱']).strip()
                            
                            values.append((
                                str(row['餐廳編號']).strip(),
                                str(row['餐廳名稱']).strip(),
                                str(row['餐點編號']).strip(),
                                str(row['菜牌編號']).strip(),
                                str(row['餐點名稱']).strip(),
                                eng_name,
                                str(row['據點']).strip() if pd.notna(row['據點']) and row['據點'] != '' else '其他',
                                row['建檔日期']
                            ))
                        
                        self.cursor.executemany(insert_sql, values)
                        success_count += len(batch)
                    
                    self.connection.commit()
            
            # 顯示處理結果
            result_message = f"成功上傳 {success_count} 筆資料！"
            if skipped_count > 0:
                result_message += f"\n已跳過 {skipped_count} 筆重複的菜牌編號。"
            
            messagebox.showinfo("上傳結果", result_message)
            return True
            
        except Exception as e:
            messagebox.showerror("錯誤", f"上傳過程中發生錯誤：\n{str(e)}")
            print("詳細錯誤：", str(e))
            return False

    def __del__(self):
        self.close_connection() 