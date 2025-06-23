import pandas as pd
import os
from tkinter import filedialog, messagebox
from module.config_sql import DB_CONFIG
import pymysql

class MenuCodeComparator:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect_database(self):
        """连接到数据库"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
        except Exception as e:
            messagebox.showerror("錯誤", f"資料庫連接失敗：\n{str(e)}")
            raise e

    def close_connection(self):
        """关闭数据库连接"""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
        except Exception as e:
            print(f"關閉連接時發生錯誤：{str(e)}")

    def get_existing_menu_codes(self):
        """从数据库获取所有已存在的菜牌编号"""
        try:
            # 确保已连接到数据库
            if not hasattr(self, 'connection') or self.connection is None:
                self.connect_database()
            # 检查连接是否有效，不再检查open属性
            try:
                # 简单执行一个查询来测试连接是否有效
                self.cursor.execute("SELECT 1")
            except:
                # 如果连接无效，重新连接
                self.connect_database()
            
            # 需要搜尋的表格清單
            tables = ['med_tpr', 'med_tpx', 'med_sun', 'menu_items']
            
            all_codes = set()
            
            # 從每個表格中獲取菜牌編號
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
                
                # 從該表格中獲取菜牌編號
                query = f"SELECT 菜牌編號 FROM {table}"
                self.cursor.execute(query)
                results = self.cursor.fetchall()
                
                # 將結果加入到集合中
                table_codes = {row[0] for row in results}
                all_codes.update(table_codes)
            
            return all_codes
            
        except Exception as e:
            messagebox.showerror("錯誤", f"獲取菜牌編號時發生錯誤：\n{str(e)}")
            print("詳細錯誤：", str(e))
            return set()

    def compare_and_save(self):
        """比较Excel文件和数据库中的菜牌编号，保存新的记录"""
        try:
            # 让用户选择Excel文件
            file_path = filedialog.askopenfilename(
                title="選擇要比對的Excel文件",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if not file_path:
                return False
                
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 确保文件包含菜牌编号列
            if '菜牌編號' not in df.columns:
                messagebox.showerror("錯誤", "Excel檔案中缺少'菜牌編號'欄位")
                return False
            
            # 获取现有的菜牌编号
            existing_codes = self.get_existing_menu_codes()
            
            # 将Excel中的菜牌编号转换为字符串以确保比较正确
            df['菜牌編號'] = df['菜牌編號'].astype(str)
            
            # 筛选出数据库中不存在的记录
            new_records = df[~df['菜牌編號'].isin(existing_codes)]
            
            if new_records.empty:
                messagebox.showinfo("提示", "沒有發現新的菜牌編號，所有記錄都已存在於資料庫中")
                return False
            
            # 创建新的文件名
            file_name, file_ext = os.path.splitext(file_path)
            new_file_path = f"{file_name}_新增{file_ext}"
            
            # 保存新记录到新文件
            new_records.to_excel(new_file_path, index=False)
            
            messagebox.showinfo("成功", f"已找到 {len(new_records)} 筆新記錄，並已保存到：\n{new_file_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("錯誤", f"比對過程中發生錯誤：\n{str(e)}")
            print("詳細錯誤：", str(e))
            return False
        finally:
            self.close_connection()

def compare_menu_codes():
    """主函数，创建比较器实例并执行比较"""
    try:
        comparator = MenuCodeComparator()
        return comparator.compare_and_save()
    except Exception as e:
        messagebox.showerror("錯誤", f"執行過程中發生錯誤：\n{str(e)}")
        print("詳細錯誤：", str(e))
        return False
