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

            # 讀取Excel檔案，跳過第一行（序號）
            df = pd.read_excel(file_path)
            print("=== 調試信息 ===")
            print("Excel檔案中的實際欄位：")
            for col in df.columns:
                print(f"'{col}'")
            print("=============")
            
            # 顯示所有欄位名稱，用於調試
            print("Excel檔案中的欄位：", df.columns.tolist())
            
            # 檢查必要欄位（不包含序號，因為會自動生成）
            required_columns = ['餐廳編號', '餐廳', '餐點編號', '菜牌編號', '餐點名稱']
            missing_columns = []
            
            # 檢查每個必要欄位是否存在
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
                    print(f"缺少欄位: {col}")
            
            if missing_columns:
                messagebox.showerror("錯誤", f"Excel檔案缺少以下欄位：\n{', '.join(missing_columns)}")
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
                餐廳 VARCHAR(100) NOT NULL,
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
            (餐廳編號, 餐廳, 餐點編號, 菜牌編號, 
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
                        str(row['餐廳']).strip(),
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
            print("Excel欄位：", df.columns.tolist())
            return False

    def __del__(self):
        self.close_connection()
