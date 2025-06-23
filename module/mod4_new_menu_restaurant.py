import os
import re
import csv
import pymysql
import datetime
from tkinter import messagebox, filedialog
from pathlib import Path
from .config_sql import DB_CONFIG

class MenuRestaurantExporter:
    def __init__(self):
        # 导出目录
        self.export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'export')
        
        # 确保导出目录存在
        os.makedirs(self.export_dir, exist_ok=True)
        
        # 要导出的表名
        self.tables = ['med_sun', 'med_tpr', 'med_tpx']
    
    def parse_date_range(self, date_range_str):
        """解析日期区间字符串，支持格式如 'YYYYMMDD-YYYYMMDD' 或单日期 'YYYYMMDD'"""
        try:
            # 检查格式
            if '-' in date_range_str:
                start_date_str, end_date_str = date_range_str.split('-')
                
                # 将 YYYYMMDD 转换为 YYYY-MM-DD 格式
                start_date = datetime.datetime.strptime(start_date_str.strip(), '%Y%m%d').date()
                end_date = datetime.datetime.strptime(end_date_str.strip(), '%Y%m%d').date()
            else:
                # 单一日期
                start_date = datetime.datetime.strptime(date_range_str.strip(), '%Y%m%d').date()
                end_date = start_date
            
            return start_date, end_date
        except Exception as e:
            raise ValueError(f"日期格式錯誤：{date_range_str}，請使用 YYYYMMDD-YYYYMMDD 格式或單一日期 YYYYMMDD。詳細錯誤：{str(e)}")
    
    def export_new_menus(self, date_range_str):
        """导出指定日期区间内的所有新菜牌"""
        try:
            start_date, end_date = self.parse_date_range(date_range_str)
            
            # 连接到 MySQL 数据库
            try:
                connection = pymysql.connect(**DB_CONFIG)
                cursor = connection.cursor()
            except pymysql.Error as e:
                messagebox.showerror("數據庫連接錯誤", f"無法連接到數據庫：{str(e)}")
                return False
            
            # 转换日期为 MySQL 可用的格式
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            export_count = 0
            export_files = []
            
            # 从每个表中导出数据
            for table_name in self.tables:
                try:
                    # 检查表是否存在
                    check_table_sql = f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = '{table_name}'
                    """
                    cursor.execute(check_table_sql)
                    if cursor.fetchone()[0] == 0:
                        continue  # 表不存在，跳过
                    
                    # 验证表结构
                    try:
                        columns_query = f"SHOW COLUMNS FROM {table_name}"
                        cursor.execute(columns_query)
                        column_names = [column[0] for column in cursor.fetchall()]
                        print(f"表 {table_name} 的列: {', '.join(column_names)}")
                        
                        if '菜牌編號' not in column_names:
                            print(f"警告: 表 {table_name} 中没有'菜牌編號'列")
                            continue
                        
                        if '建檔日期' not in column_names:
                            print(f"警告: 表 {table_name} 中没有'建檔日期'列")
                            continue
                    except pymysql.Error as e:
                        print(f"获取表 {table_name} 结构时出错: {str(e)}")
                        continue
                    
                    # 第一步：获取该表中开始日期之前的所有菜牌编号
                    existing_menu_codes = set()
                    query = f"""
                    SELECT DISTINCT 菜牌編號 FROM {table_name}
                    WHERE 建檔日期 < %s 
                    AND 菜牌編號 IS NOT NULL 
                    AND 菜牌編號 != ''
                    """
                    cursor.execute(query, (start_date_str,))
                    for row in cursor.fetchall():
                        if row[0]:  # 确保菜牌编号不为空
                            existing_menu_codes.add(row[0])
                    
                    print(f"表 {table_name} 中历史菜牌编号总数: {len(existing_menu_codes)}")
                    
                    # 第二步：查询该日期区间内的数据
                    query = f"""
                    SELECT * FROM {table_name}
                    WHERE 建檔日期 BETWEEN %s AND %s
                    """
                    cursor.execute(query, (start_date_str, end_date_str))
                    results = cursor.fetchall()
                    
                    if results:
                        # 获取列名
                        columns_query = f"SHOW COLUMNS FROM {table_name}"
                        cursor.execute(columns_query)
                        column_names = [column[0] for column in cursor.fetchall()]
                        
                        # 查找菜牌编号列的索引
                        menu_code_index = column_names.index('菜牌編號') if '菜牌編號' in column_names else None
                        
                        if menu_code_index is not None:
                            # 筛选出新菜牌（不在现有菜牌编号集合中的）
                            new_menu_records = []
                            table_new_menus = set()  # 记录当前表中找到的新菜牌
                            
                            # 统计符合日期条件但是菜牌编号为空的记录
                            empty_code_count = 0
                            
                            for record in results:
                                menu_code = record[menu_code_index]
                                
                                if not menu_code or menu_code.strip() == '':
                                    empty_code_count += 1
                                    continue
                                    
                                if menu_code not in existing_menu_codes:
                                    new_menu_records.append(record)
                                    existing_menu_codes.add(menu_code)  # 添加到已处理集合，避免同一表中重复
                                    table_new_menus.add(menu_code)  # 记录新找到的菜牌
                            
                            print(f"表 {table_name} 中找到 {len(table_new_menus)} 个新菜牌编号")
                            if empty_code_count > 0:
                                print(f"表 {table_name} 中有 {empty_code_count} 条记录的菜牌编号为空")
                            
                            if len(results) - empty_code_count - len(new_menu_records) > 0:
                                print(f"表 {table_name} 中有 {len(results) - empty_code_count - len(new_menu_records)} 条记录的菜牌编号已存在")
                            
                            if new_menu_records:
                                # 构建 CSV 文件名
                                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                                file_name = f"new_menus_{table_name}_{timestamp}.csv"
                                file_path = os.path.join(self.export_dir, file_name)
                                
                                # 导出为 CSV
                                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                                    csv_writer = csv.writer(csv_file)
                                    csv_writer.writerow(column_names)
                                    csv_writer.writerows(new_menu_records)
                                
                                export_count += len(new_menu_records)
                                export_files.append(file_path)
                                
                                print(f"已导出 {len(new_menu_records)} 条新菜牌数据到 {file_path}")
                            else:
                                print(f"表 {table_name} 没有需要导出的新菜牌数据")
                        else:
                            print(f"表 {table_name} 中找不到菜牌编号列")
                    else:
                        print(f"表 {table_name} 在日期区间内没有记录")
                
                except pymysql.Error as e:
                    print(f"處理表 {table_name} 時出錯: {str(e)}")
                    continue
                except Exception as e:
                    print(f"處理表 {table_name} 時發生未知錯誤: {str(e)}")
                    continue
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            if export_count > 0:
                messagebox.showinfo("導出完成", f"成功導出 {export_count} 條新菜牌數據，共 {len(export_files)} 個文件，保存在 {self.export_dir} 目錄下。")
                return True
            else:
                messagebox.showinfo("無數據", f"在指定日期 {date_range_str} 範圍內沒有找到新菜牌數據。")
                return False
            
        except ValueError as e:
            messagebox.showerror("值錯誤", str(e))
            return False
        except Exception as e:
            messagebox.showerror("錯誤", f"導出新菜牌失敗：{str(e)}")
            return False
    
    def export_new_restaurants(self, date_range_str):
        """导出指定日期区间内的新餐厅（不包括已存在的餐厅）"""
        try:
            start_date, end_date = self.parse_date_range(date_range_str)
            
            # 连接到 MySQL 数据库
            try:
                connection = pymysql.connect(**DB_CONFIG)
                cursor = connection.cursor()
            except pymysql.Error as e:
                messagebox.showerror("數據庫連接錯誤", f"無法連接到數據庫：{str(e)}")
                return False
            
            # 转换日期为 MySQL 可用的格式
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            export_count = 0
            export_files = []
            
            # 分别处理每个表中的新餐厅
            for table_name in self.tables:
                try:
                    # 检查表是否存在
                    check_table_sql = f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = '{table_name}'
                    """
                    cursor.execute(check_table_sql)
                    if cursor.fetchone()[0] == 0:
                        print(f"表 {table_name} 不存在，跳过处理")
                        continue  # 表不存在，跳过
                    
                    # 验证表结构
                    try:
                        columns_query = f"SHOW COLUMNS FROM {table_name}"
                        cursor.execute(columns_query)
                        column_names = [column[0] for column in cursor.fetchall()]
                        print(f"表 {table_name} 的列: {', '.join(column_names)}")
                        
                        if '餐廳名稱' not in column_names:
                            print(f"警告: 表 {table_name} 中没有'餐廳名稱'列")
                            continue
                        
                        if '據點' not in column_names:
                            print(f"警告: 表 {table_name} 中没有'據點'列")
                            continue
                        
                        if '建檔日期' not in column_names:
                            print(f"警告: 表 {table_name} 中没有'建檔日期'列")
                            continue
                    except pymysql.Error as e:
                        print(f"获取表 {table_name} 结构时出错: {str(e)}")
                        continue
                    
                    # 第一步：获取该表中开始日期之前的所有餐厅和据点组合
                    existing_restaurants = set()
                    query = f"""
                    SELECT DISTINCT 餐廳名稱, 據點 FROM {table_name}
                    WHERE 建檔日期 < %s 
                    AND 餐廳名稱 IS NOT NULL 
                    AND 餐廳名稱 != ''
                    AND 據點 IS NOT NULL
                    AND 據點 != ''
                    """
                    cursor.execute(query, (start_date_str,))
                    for row in cursor.fetchall():
                        if row[0] and row[1]:  # 确保餐厅名称和据点都不为空
                            existing_restaurants.add((row[0], row[1]))
                    
                    print(f"表 {table_name} 中历史餐厅-据点组合总数: {len(existing_restaurants)}")
                    
                    # 第二步：查询该日期区间内的数据
                    query = f"""
                    SELECT * FROM {table_name}
                    WHERE 建檔日期 BETWEEN %s AND %s
                    """
                    cursor.execute(query, (start_date_str, end_date_str))
                    results = cursor.fetchall()
                    
                    if results:
                        # 获取列名
                        columns_query = f"SHOW COLUMNS FROM {table_name}"
                        cursor.execute(columns_query)
                        column_names = [column[0] for column in cursor.fetchall()]
                        
                        # 查找餐厅名称和据点列的索引
                        restaurant_index = column_names.index('餐廳名稱') if '餐廳名稱' in column_names else None
                        location_index = column_names.index('據點') if '據點' in column_names else None
                        
                        if restaurant_index is not None and location_index is not None:
                            # 筛选出新餐厅（不在现有餐厅集合中的）
                            new_restaurant_records = []
                            table_new_restaurants = set()  # 记录当前表中找到的新餐厅
                            
                            # 统计符合日期条件但是餐厅名称或据点为空的记录
                            empty_name_count = 0
                            empty_location_count = 0
                            
                            for record in results:
                                restaurant_name = record[restaurant_index]
                                location = record[location_index]
                                
                                if not restaurant_name or restaurant_name.strip() == '':
                                    empty_name_count += 1
                                    continue
                                    
                                if not location or location.strip() == '':
                                    empty_location_count += 1
                                    continue
                                    
                                if (restaurant_name, location) not in existing_restaurants:
                                    new_restaurant_records.append(record)
                                    existing_restaurants.add((restaurant_name, location))  # 添加到已处理集合，避免同一表中重复
                                    table_new_restaurants.add((restaurant_name, location))  # 记录新找到的餐厅
                            
                            print(f"表 {table_name} 中找到 {len(table_new_restaurants)} 个新餐厅-据点组合")
                            if empty_name_count > 0:
                                print(f"表 {table_name} 中有 {empty_name_count} 条记录的餐厅名称为空")
                            if empty_location_count > 0:
                                print(f"表 {table_name} 中有 {empty_location_count} 条记录的据点为空")
                            
                            if len(results) - empty_name_count - empty_location_count - len(new_restaurant_records) > 0:
                                print(f"表 {table_name} 中有 {len(results) - empty_name_count - empty_location_count - len(new_restaurant_records)} 条记录的餐厅-据点组合已存在")
                            
                            if new_restaurant_records:
                                # 构建 CSV 文件名
                                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                                file_name = f"new_restaurants_{table_name}_{timestamp}.csv"
                                file_path = os.path.join(self.export_dir, file_name)
                                
                                # 导出为 CSV
                                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                                    csv_writer = csv.writer(csv_file)
                                    csv_writer.writerow(column_names)
                                    csv_writer.writerows(new_restaurant_records)
                                
                                export_count += len(new_restaurant_records)
                                export_files.append(file_path)
                                
                                print(f"已导出 {len(new_restaurant_records)} 条新餐厅数据到 {file_path}")
                            else:
                                print(f"表 {table_name} 没有需要导出的新餐厅数据")
                        else:
                            print(f"表 {table_name} 中找不到餐厅名称列或据点列")
                    else:
                        print(f"表 {table_name} 在日期区间内没有记录")
                
                except pymysql.Error as e:
                    print(f"處理表 {table_name} 時出錯: {str(e)}")
                    continue
                except Exception as e:
                    print(f"處理表 {table_name} 時發生未知錯誤: {str(e)}")
                    continue
            
            # 关闭数据库连接
            cursor.close()
            connection.close()
            
            if export_count > 0:
                messagebox.showinfo("導出完成", f"成功導出 {export_count} 條新餐廳數據，共 {len(export_files)} 個文件，保存在 {self.export_dir} 目錄下。")
                return True
            else:
                messagebox.showinfo("無數據", f"在指定日期 {date_range_str} 範圍內沒有找到新餐廳數據。")
                return False
                
        except ValueError as e:
            messagebox.showerror("值錯誤", str(e))
            return False
        except Exception as e:
            messagebox.showerror("錯誤", f"導出新餐廳失敗：{str(e)}")
            return False

# 导出新菜牌数据的函数，供UI调用
def export_new_menus(date_range):
    exporter = MenuRestaurantExporter()
    return exporter.export_new_menus(date_range)

# 导出新餐厅数据的函数，供UI调用
def export_new_restaurants(date_range):
    exporter = MenuRestaurantExporter()
    return exporter.export_new_restaurants(date_range)
