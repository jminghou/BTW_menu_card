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

        # 創建篩選按鈕
        btn_filter = tk.Button(
            main_frame,
            text="篩選菜牌",
            command=self.filter_menu_codes,
            height=2
        )
        btn_filter.pack(pady=(0,10), fill='x')

        # 新增餐廳篩選按鈕
        btn_filter_restaurant = tk.Button(
            main_frame,
            text="篩選餐廳牌",
            command=self.filter_restaurants,
            height=2
        )
        btn_filter_restaurant.pack(pady=(0,20), fill='x')

        # 新增比對菜牌編號按鈕
        btn_compare = tk.Button(
            main_frame,
            text="比對菜牌編號",
            command=self.compare_menu_codes,
            height=2
        )
        btn_compare.pack(pady=(0,10), fill='x')

        # 上傳資料庫改成獨立一排的長按鈕
        btn_upload = tk.Button(
            main_frame,
            text="上傳資料庫",
            command=self.upload_to_database,
            height=2
        )
        btn_upload.pack(pady=(0,10), fill='x')

        # 新增下載菜牌按鈕
        btn_download = tk.Button(
            main_frame,
            text="下載菜牌",
            command=self.download_all,
            height=2
        )
        btn_download.pack(pady=(0,10), fill='x')

        # 創建搜尋框架（移到底部）
        search_frame = ttk.LabelFrame(main_frame, text="搜尋菜牌 (可複製多個編號，每行一個)", padding=(10, 5))
        search_frame.pack(fill='both', expand=True, pady=(0, 10))

        # 將 Entry 改為 Text，並設定更大的高度
        self.entry_menu_code = tk.Text(search_frame, height=15, width=20)
        self.entry_menu_code.pack(side='left', padx=(0, 5), fill='both', expand=True)
        
        # 添加垂直滾動條
        scrollbar = ttk.Scrollbar(search_frame, orient="vertical", command=self.entry_menu_code.yview)
        scrollbar.pack(side='right', fill='y')
        self.entry_menu_code.configure(yscrollcommand=scrollbar.set)
        
        # 搜尋按鈕
        btn_search = ttk.Button(
            main_frame,
            text="搜尋",
            command=self.search_menu_code
        )
        btn_search.pack(fill='x')  # 調整按鈕位置

        # 新增轉換CSV到TXT按鈕
        btn_convert_csv = tk.Button(
            main_frame,
            text="轉換CSV到TXT",
            command=self.convert_csv_files,
            height=2
        )
        btn_convert_csv.pack(pady=(0,10), fill='x')

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
        
