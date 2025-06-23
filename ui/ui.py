import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
from module.mod_number import process_menu_codes
from module.mod_sql import DatabaseUploader
from module.mod_difference import MenuDifferenceCalculator
from module.mod_clean import clean_excel_file as clean_excel_file_original
from module.mod_calendar import clean_excel_file as clean_excel_file_calendar_func
from module.mod_search import search_menu_codes
from module.mod_sql_function import DatabaseFunction
from module.mod_dif_restairamt import RestaurantDifferenceCalculator
from module.mod2_compare import compare_menu_codes
from module.mod2_utf8 import convert_csv_to_unicode_txt
from module.mod4_new_menu_restaurant import export_new_menus, export_new_restaurants

class MenuCardUI:
    def __init__(self, root=None):
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root
            
        self.root.title("菜牌管理程式")
        self.root.geometry("400x600")  # 調整視窗大小
        self.entry_menu_code = None
        self.create_ui()
        
    def create_ui(self):
        # 創建主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')

        # 創建功能按鈕框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        # 設定按鈕共同樣式
        button_width = 12
        button_height = 2

        # 創建第一排按鈕（兩個並排）
        btn_clean = tk.Button(
            button_frame,
            text="資料清洗",
            command=self.clean_excel_file,
            width=button_width,
            height=button_height
        )
        btn_clean.pack(side='left', expand=True, padx=5)

        btn_generate = tk.Button(
            button_frame,
            text="菜牌編號產生",
            command=self.process_menu_codes_ui,
            width=button_width,
            height=button_height
        )
        btn_generate.pack(side='left', expand=True, padx=5)

        # 上傳資料庫改成獨立一排的長按鈕
        btn_upload = tk.Button(
            main_frame,
            text="上傳資料庫",
            command=self.upload_to_database,
            height=2
        )
        btn_upload.pack(pady=(0,10), fill='x')

        # 創建"下載無英文菜單"和"上傳菜單英文名稱"按鈕框架（替代原來的"篩選菜牌"按鈕）
        no_english_frame = tk.Frame(main_frame)
        no_english_frame.pack(fill='x', pady=(0, 10))

        # 下載無英文菜單
        btn_download_no_english = tk.Button(
            no_english_frame,
            text="下載無英文菜單",
            command=self.download_no_english,
            width=button_width,
            height=button_height
        )
        btn_download_no_english.pack(side='left', expand=True, padx=5)

        # 上傳菜單英文名稱
        btn_upload_english = tk.Button(
            no_english_frame,
            text="上傳菜單英文名稱",
            command=self.upload_english,
            width=button_width,
            height=button_height
        )
        btn_upload_english.pack(side='left', expand=True, padx=5)

        # 刪除重複菜牌編號按鈕
        btn_remove_duplicates = tk.Button(
            main_frame,
            text="刪除重複菜牌編號",
            command=self.remove_duplicates,
            height=2
        )
        btn_remove_duplicates.pack(pady=(0,10), fill='x')

        # 新增兩組文字輸入框和按鈕
        # 第一組：新菜牌
        new_menu_frame = tk.Frame(main_frame)
        new_menu_frame.pack(fill='x', pady=(0, 10))
        
        # 新菜牌輸入框
        self.entry_new_menu = tk.Entry(new_menu_frame)
        self.entry_new_menu.pack(side='left', fill='x', expand=True, padx=(0, 5))
        # 添加預視文字
        self.entry_new_menu.insert(0, "YYYYMMDD-YYYYMMDD或YYYYMMDD")
        # 設置焦點事件，當獲得焦點時清空預設文字
        self.entry_new_menu.bind("<FocusIn>", lambda event: self.on_entry_focus_in(event, self.entry_new_menu, "YYYYMMDD-YYYYMMDD或YYYYMMDD"))
        # 設置失去焦點事件，當輸入框為空時恢復預設文字
        self.entry_new_menu.bind("<FocusOut>", lambda event: self.on_entry_focus_out(event, self.entry_new_menu, "YYYYMMDD-YYYYMMDD或YYYYMMDD"))
        
        # 新菜牌按鈕
        btn_new_menu = tk.Button(
            new_menu_frame,
            text="新菜牌",
            height=1,
            width=button_width,
            command=self.export_new_menus
        )
        btn_new_menu.pack(side='right')

        # 第二組：新餐廳
        new_restaurant_frame = tk.Frame(main_frame)
        new_restaurant_frame.pack(fill='x', pady=(0, 10))
        
        # 新餐廳輸入框
        self.entry_new_restaurant = tk.Entry(new_restaurant_frame)
        self.entry_new_restaurant.pack(side='left', fill='x', expand=True, padx=(0, 5))
        # 添加預視文字
        self.entry_new_restaurant.insert(0, "YYYYMMDD-YYYYMMDD或YYYYMMDD")
        # 設置焦點事件，當獲得焦點時清空預設文字
        self.entry_new_restaurant.bind("<FocusIn>", lambda event: self.on_entry_focus_in(event, self.entry_new_restaurant, "YYYYMMDD-YYYYMMDD或YYYYMMDD"))
        # 設置失去焦點事件，當輸入框為空時恢復預設文字
        self.entry_new_restaurant.bind("<FocusOut>", lambda event: self.on_entry_focus_out(event, self.entry_new_restaurant, "YYYYMMDD-YYYYMMDD或YYYYMMDD"))
        
        # 新餐廳按鈕
        btn_new_restaurant = tk.Button(
            new_restaurant_frame,
            text="新餐廳",
            height=1,
            width=button_width,
            command=self.export_new_restaurants
        )
        btn_new_restaurant.pack(side='right')

        # 新增下載菜牌按鈕
        btn_download = tk.Button(
            main_frame,
            text="下載菜牌",
            command=self.download_all,
            height=2
        )
        btn_download.pack(pady=(0,10), fill='x')

        # 新增轉換CSV到TXT按鈕
        btn_convert_csv = tk.Button(
            main_frame,
            text="轉換CSV到TXT",
            command=self.convert_csv_files,
            height=2
        )
        btn_convert_csv.pack(pady=(0,10), fill='x')

    def on_entry_focus_in(self, event, entry, placeholder_text):
        """當輸入框獲得焦點時，如果內容是預設文字則清空"""
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)

    def on_entry_focus_out(self, event, entry, placeholder_text):
        """當輸入框失去焦點時，如果內容為空則恢復預設文字"""
        if entry.get() == '':
            entry.insert(0, placeholder_text)

    def run(self):
        self.root.mainloop()
        
    def process_menu_codes_ui(self):
        try:
            # 讓用戶選擇多個Excel文件
            file_paths = filedialog.askopenfilenames(
                title="選擇要產生編號的Excel文件",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if not file_paths:
                return
                
            success_files = []
            error_files = []
            
            for file_path in file_paths:
                new_file_path, error = process_menu_codes(file_path)
                
                if error:
                    error_files.append(f"{os.path.basename(file_path)}: {error}")
                else:
                    success_files.append(new_file_path)
            
            # 顯示處理結果
            result_message = ""
            if success_files:
                result_message += "成功處理的檔案：\n" + "\n".join([f"- {os.path.basename(f)}" for f in success_files])
            
            if error_files:
                if result_message:
                    result_message += "\n\n"
                result_message += "處理失敗的檔案：\n" + "\n".join([f"- {e}" for e in error_files])
            
            if success_files:
                messagebox.showinfo("處理完成", result_message)
            else:
                messagebox.showerror("處理失敗", result_message)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"處理過程中發生錯誤：{str(e)}")

    def upload_to_database(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            uploader = DatabaseUploader()
            uploader.upload_file(file_path)

    def filter_menu_codes(self):
        calculator = MenuDifferenceCalculator()
        calculator.calculate_difference()

    def search_menu_code(self):
        # 獲取文本框中的所有菜牌編號
        menu_codes = self.entry_menu_code.get('1.0', tk.END).strip().split('\n')
        menu_codes = [code.strip() for code in menu_codes if code.strip()]
        search_menu_codes(menu_codes)

    def check_duplicates(self):
        db_function = DatabaseFunction()
        db_function.check_duplicates()

    def remove_duplicates(self):
        db_function = DatabaseFunction()
        db_function.remove_duplicates()

    def download_all(self):
        db_function = DatabaseFunction()
        db_function.download_all()

    def filter_restaurants(self):
        calculator = RestaurantDifferenceCalculator()
        calculator.calculate_difference()
        
    def clean_excel_file(self):
        clean_excel_file_original()

    def clean_excel_file_calendar(self):
        clean_excel_file_calendar_func()
        
    def compare_menu_codes(self):
        compare_menu_codes()
        
    def convert_csv_files(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇要轉換的CSV文件",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_paths:
            convert_csv_to_unicode_txt(file_paths)
        
    def download_no_english(self):
        from module.mod3_no_english import download_no_english_menus
        download_no_english_menus()
        
    def upload_english(self):
        # 上傳菜單英文名稱功能
        from module.mod3_input_english import upload_english_names
        upload_english_names()
        
    def export_new_menus(self):
        """導出指定日期區間內的新菜牌"""
        date_range = self.entry_new_menu.get().strip()
        if not date_range:
            messagebox.showwarning("警告", "請輸入日期區間，格式為 YYYYMMDD-YYYYMMDD 或單一日期 YYYYMMDD")
            return
        
        # 如果還是預設值，則視為未輸入
        if date_range == "YYYYMMDD-YYYYMMDD或YYYYMMDD":
            messagebox.showwarning("警告", "請輸入日期區間，格式為 YYYYMMDD-YYYYMMDD 或單一日期 YYYYMMDD")
            return
        
        export_new_menus(date_range)
        
    def export_new_restaurants(self):
        """導出指定日期區間內的新餐廳"""
        date_range = self.entry_new_restaurant.get().strip()
        if not date_range:
            messagebox.showwarning("警告", "請輸入日期區間，格式為 YYYYMMDD-YYYYMMDD 或單一日期 YYYYMMDD")
            return
        
        # 如果還是預設值，則視為未輸入
        if date_range == "YYYYMMDD-YYYYMMDD或YYYYMMDD":
            messagebox.showwarning("警告", "請輸入日期區間，格式為 YYYYMMDD-YYYYMMDD 或單一日期 YYYYMMDD")
            return
        
        export_new_restaurants(date_range)
        
