import pandas as pd
from datetime import datetime
from tkinter import messagebox
import pymysql
import os

class DatabaseUploader:
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

    def upload_file(self, file_path):
        try:
            # 確保資料庫連接是開啟的
            if not hasattr(self, 'connection') or self.connection.open == False:
                self.connect_database()

            # 讀取Excel檔案
            df = pd.read_excel(file_path)
            
            # 檢查必要欄位
            required_columns = ['餐廳編號', '餐廳名稱', '餐點編號', '菜牌編號', '餐點名稱', '英文名稱']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("錯誤", f"Excel檔案缺少以下欄位：\n{', '.join(missing_columns)}")
                return False

            # 檢查資料庫中現有的菜牌編號
            check_sql = "SELECT 菜牌編號 FROM menu_items"
            self.cursor.execute(check_sql)
            existing_codes = {row[0] for row in self.cursor.fetchall()}

            # 檢查新資料中的菜牌編號
            new_codes = set(df['菜牌編號'].astype(str))
            duplicate_codes = new_codes.intersection(existing_codes)

            if duplicate_codes:
                # 顯示重複的菜牌編號
                duplicate_list = '\n'.join(sorted(duplicate_codes))
                messagebox.showwarning("警告", 
                    f"發現重複的菜牌編號，這些記錄將被跳過：\n{duplicate_list}")
                
                # 過濾掉重複的記錄
                df = df[~df['菜牌編號'].astype(str).isin(duplicate_codes)]
                
                if df.empty:
                    messagebox.showinfo("提示", "所有記錄都已存在於資料庫中，沒有新資料需要上傳")
                    return False

            # 添加建檔日期
            df['建檔日期'] = datetime.now()

            # 確保英文名稱欄位存在
            if '英文名稱' not in df.columns:
                df['英文名稱'] = ''

            # 創建資料表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS menu_items (
                序號 INT AUTO_INCREMENT PRIMARY KEY,
                餐廳編號 VARCHAR(10) NOT NULL,
                餐廳名稱 VARCHAR(100) NOT NULL,
                餐點編號 VARCHAR(10) NOT NULL,
                菜牌編號 VARCHAR(20) NOT NULL,
                餐點名稱 VARCHAR(100) NOT NULL,
                英文名稱 VARCHAR(100),
                建檔日期 DATETIME NOT NULL
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()

            # 準備插入語句（不包含序號，因為是自動生成的）
            insert_sql = """
            INSERT INTO menu_items 
            (餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 
             餐點名稱, 英文名稱, 建檔日期)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            # 批次處理資料
            batch_size = 100
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                values = [
                    (
                        str(row['餐廳編號']).strip(),
                        str(row['餐廳名稱']).strip(),
                        str(row['餐點編號']).strip(),
                        str(row['菜牌編號']).strip(),
                        str(row['餐點名稱']).strip(),
                        str(row['英文名稱']).strip() if pd.notna(row['英文名稱']) else '',
                        row['建檔日期']
                    )
                    for _, row in batch.iterrows()
                ]
                
                # 執行批次插入
                self.cursor.executemany(insert_sql, values)
                self.connection.commit()

            messagebox.showinfo("成功", "資料已成功上傳到資料庫！")
            return True
            
        except Exception as e:
            messagebox.showerror("錯誤", f"上傳過程中發生錯誤：\n{str(e)}")
            print("詳細錯誤：", str(e))
            return False

    def __del__(self):
        self.close_connection()
