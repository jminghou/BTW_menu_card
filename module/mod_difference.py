import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Text
from tkinter import ttk
from datetime import datetime
import csv
from .mod_sql import DatabaseUploader

class MenuDifferenceCalculator:
    def __init__(self):
        self.window = None
        self.text_area = None
        self.filtered_codes = []  # 儲存篩選後的菜牌編號

    def calculate_difference(self):
        try:
            # 選擇第一個檔案（主要檔案）
            file1 = filedialog.askopenfilename(
                title="請選擇主要的Excel檔案",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not file1:
                return

            # 選擇第二個檔案（參考檔案）
            file2 = filedialog.askopenfilename(
                title="請選擇用於篩選的Excel檔案",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not file2:
                return

            # 讀取兩個Excel檔案
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)

            # 確認兩個檔案都有 '菜牌編號' 欄位
            if '菜牌編號' not in df1.columns or '菜牌編號' not in df2.columns:
                messagebox.showerror("錯誤", "Excel檔案中缺少 '菜牌編號' 欄位")
                return

            # 取得兩個檔案的菜牌編號集合
            set1 = set(df1['菜牌編號'].astype(str))
            set2 = set(df2['菜牌編號'].astype(str))

            # 計算差集（在set1中但不在set2中的編號）
            difference = sorted(list(set1 - set2))
            self.filtered_codes = difference  # 儲存篩選結果
            self.create_result_window(difference)

        except Exception as e:
            messagebox.showerror("錯誤", f"處理檔案時發生錯誤：\n{str(e)}")

    def create_result_window(self, difference):
        # 如果已經有視窗，先關閉它
        if self.window and self.window.winfo_exists():
            self.window.destroy()

        # 創建新視窗
        self.window = tk.Toplevel()
        self.window.title("篩選結果")
        self.window.geometry("400x500")

        # 創建框架
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 添加標籤
        label = ttk.Label(frame, text=f"找到 {len(difference)} 個未重複的菜牌編號：")
        label.pack(pady=(0, 10))

        # 創建文字區域
        self.text_area = Text(frame, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # 添加捲軸
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.configure(yscrollcommand=scrollbar.set)

        # 插入結果
        for code in difference:
            self.text_area.insert(tk.END, f"{code}\n")

        # 創建按鈕框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        # 複製按鈕
        copy_button = ttk.Button(button_frame, text="複製全部", command=self.copy_to_clipboard)
        copy_button.pack(side=tk.LEFT, padx=5)

        # 匯出按鈕
        export_button = ttk.Button(button_frame, text="匯出篩選結果", command=self.export_filtered_data)
        export_button.pack(side=tk.LEFT, padx=5)

    def copy_to_clipboard(self):
        if self.text_area:
            self.window.clipboard_clear()
            self.window.clipboard_append(self.text_area.get("1.0", tk.END))
            messagebox.showinfo("成功", "已複製到剪貼簿")

    def export_filtered_data(self):
        try:
            if not self.filtered_codes:
                messagebox.showerror("錯誤", "沒有可匯出的資料")
                return

            # 使用 DatabaseUploader 類別
            db = DatabaseUploader()
            
            # 查詢資料
            results = db.search_menu_codes(self.filtered_codes)

            # 檢查哪些編號沒有在查詢結果中
            found_codes = {row[5] for row in results}  # 現在菜牌編號是第6個欄位，因為第1個欄位是表名
            missing_codes = set(self.filtered_codes) - found_codes
            
            if missing_codes:
                missing_list = '\n'.join(sorted(missing_codes))
                if not messagebox.askyesno(
                    "警告",
                    f"以下菜牌編號在資料庫中找不到對應資料：\n\n{missing_list}\n\n是否要繼續匯出其他有建檔的項目？"
                ):
                    return

            if not results:
                messagebox.showerror("錯誤", "在資料庫中找不到相關記錄")
                return

            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"menu_filtered_export_{current_time}.csv"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=default_filename,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # 寫入CSV檔案
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 寫入標題，加入表名欄位
                headers = ["資料表", "序號", "餐廳編號", "餐廳名稱", "餐點編號", "菜牌編號", "餐點名稱", "英文名稱", "建檔日期"]
                writer.writerow(headers)
                # 寫入資料
                for row in results:
                    writer.writerow(row)
            
            messagebox.showinfo("成功", f"成功匯出 {len(results)} 筆資料至 {file_path}")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出過程中發生錯誤：\n{str(e)}")

class DatabaseExporter:
    def export_to_txt(self):
        try:
            # 取得當前日期時間作為檔名
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"menu_export_{current_time}.txt"
            
            # 開啟檔案選擇對話框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialfile=default_filename,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # 使用 DatabaseUploader 類別
            db = DatabaseUploader()
            try:
                # 查詢資料
                query = """
                SELECT 序號, 餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 餐點名稱, 英文名稱
                FROM menu_items
                ORDER BY 序號
                """
                db.cursor.execute(query)
                results = db.cursor.fetchall()
                
                # 寫入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 寫入標題列
                    headers = ["序號", "餐廳編號", "餐廳名稱", "餐點編號", "菜牌編號", "餐點名稱", "英文名稱"]
                    f.write('\t'.join(headers) + '\n')
                    
                    # 寫入資料列
                    for row in results:
                        # 將所有欄位轉換為字串並去除空白
                        formatted_row = [str(item).strip() if item is not None else '' for item in row]
                        f.write('\t'.join(formatted_row) + '\n')
                
                messagebox.showinfo("成功", f"資料已成功匯出至：\n{file_path}")
                return True
                
            finally:
                db.close_connection()
            
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出過程中發生錯誤：\n{str(e)}")
            return False 