import pandas as pd
from tkinter import messagebox, filedialog
from datetime import datetime
from .mod_sql import DatabaseUploader

class DatabaseFunction:
    def __init__(self):
        self.db = DatabaseUploader()

    def check_duplicates(self):
        """檢查資料庫中重複的菜牌編號"""
        try:
            query = """
            SELECT 菜牌編號, COUNT(*) as count
            FROM menu_items
            GROUP BY 菜牌編號
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            """
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()

            if not results:
                messagebox.showinfo("檢查結果", "資料庫中沒有重複的菜牌編號")
                return

            # 創建結果視窗
            window = tk.Toplevel()
            window.title("重複的菜牌編號")
            window.geometry("400x500")

            # 創建框架
            frame = ttk.Frame(window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)

            # 添加標籤
            label = ttk.Label(frame, text=f"找到 {len(results)} 個重複的菜牌編號：")
            label.pack(pady=(0, 10))

            # 創建文字區域
            text_area = tk.Text(frame, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True)

            # 添加捲軸
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_area.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_area.configure(yscrollcommand=scrollbar.set)

            # 插入結果
            for code, count in results:
                text_area.insert(tk.END, f"菜牌編號: {code} (重複 {count} 次)\n")

            # 複製按鈕
            def copy_to_clipboard():
                window.clipboard_clear()
                window.clipboard_append(text_area.get("1.0", tk.END))
                messagebox.showinfo("成功", "已複製到剪貼簿")

            copy_button = ttk.Button(frame, text="複製全部", command=copy_to_clipboard)
            copy_button.pack(pady=10)

        except Exception as e:
            messagebox.showerror("錯誤", f"檢查重複時發生錯誤：\n{str(e)}")
        finally:
            self.db.close_connection()

    def remove_duplicates(self):
        """刪除資料庫中重複的菜牌編號"""
        try:
            # 定義需要檢查的表格
            tables = ['menu_items', 'med_tpr', 'med_tpx', 'med_sun']
            all_duplicates = {}
            
            # 檢查每個表中的重複項
            for table in tables:
                check_query = f"""
                SELECT 菜牌編號, COUNT(*) as count
                FROM {table}
                GROUP BY 菜牌編號
                HAVING COUNT(*) > 1
                """
                self.db.cursor.execute(check_query)
                duplicates = self.db.cursor.fetchall()
                
                if duplicates:
                    all_duplicates[table] = len(duplicates)
            
            if not all_duplicates:
                messagebox.showinfo("提示", "所有表格中都沒有重複的菜牌編號")
                return
            
            # 構建提示訊息
            duplicate_msg = "發現以下重複的菜牌編號：\n"
            for table, count in all_duplicates.items():
                duplicate_msg += f"- {table}: {count} 個重複項\n"
            duplicate_msg += "\n是否要刪除重複項目？（將保留每個編號的最早建檔日期記錄）"
            
            # 詢問用戶是否要刪除
            if not messagebox.askyesno("確認", duplicate_msg):
                return
            
            # 執行刪除操作
            for table in tables:
                # 首先獲取每個菜牌編號最早的建檔日期記錄的ID
                self.db.cursor.execute(f"""
                CREATE TEMPORARY TABLE IF NOT EXISTS temp_earliest_records
                SELECT MIN(序號) as 最早序號, 菜牌編號
                FROM {table}
                GROUP BY 菜牌編號
                """)
                
                # 刪除不在最早記錄列表中的重複項目
                delete_query = f"""
                DELETE FROM {table}
                WHERE 序號 NOT IN (
                    SELECT 最早序號 FROM temp_earliest_records
                )
                AND 菜牌編號 IN (
                    SELECT 菜牌編號 FROM (
                        SELECT 菜牌編號
                        FROM {table}
                        GROUP BY 菜牌編號
                        HAVING COUNT(*) > 1
                    ) AS duplicates
                )
                """
                self.db.cursor.execute(delete_query)
                
                # 清理臨時表
                self.db.cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_earliest_records")
            
            # 提交更改
            self.db.connection.commit()
            
            # 再次檢查是否還有重複項
            remaining_duplicates = {}
            for table in tables:
                check_query = f"""
                SELECT 菜牌編號, COUNT(*) as count
                FROM {table}
                GROUP BY 菜牌編號
                HAVING COUNT(*) > 1
                """
                self.db.cursor.execute(check_query)
                duplicates = self.db.cursor.fetchall()
                
                if duplicates:
                    remaining_duplicates[table] = len(duplicates)
            
            # 計算刪除後的情況
            deleted_counts = {}
            for table in tables:
                self.db.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.db.cursor.fetchone()[0]
                deleted_counts[table] = count
            
            # 構建成功訊息
            if remaining_duplicates:
                warning_msg = "已嘗試刪除重複的菜牌編號，但以下表格中仍有重複項：\n"
                for table, count in remaining_duplicates.items():
                    warning_msg += f"- {table}: 剩餘 {count} 個重複項\n"
                warning_msg += "\n各表格當前記錄數：\n"
                for table, count in deleted_counts.items():
                    warning_msg += f"- {table}: {count} 筆記錄\n"
                messagebox.showwarning("警告", warning_msg)
            else:
                success_msg = "已成功刪除所有重複的菜牌編號。各表格當前記錄數：\n"
                for table, count in deleted_counts.items():
                    success_msg += f"- {table}: {count} 筆記錄\n"
                messagebox.showinfo("成功", success_msg)

        except Exception as e:
            messagebox.showerror("錯誤", f"刪除重複時發生錯誤：\n{str(e)}")
            # 打印詳細錯誤信息以便調試
            import traceback
            print(traceback.format_exc())
        finally:
            self.db.close_connection()

    def download_all(self):
        """下載資料庫中所有菜牌資料"""
        try:
            # 取得當前日期時間作為檔名
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"menu_all_{current_time}.xlsx"
            
            # 讓使用者選擇儲存位置
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=default_filename,
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # 查詢所有資料
            query = """
            SELECT 序號, 餐廳編號, 餐廳名稱, 餐點編號, 菜牌編號, 餐點名稱, 英文名稱, 建檔日期
            FROM menu_items
            ORDER BY 序號
            """
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            
            if not results:
                messagebox.showinfo("提示", "資料庫中沒有資料")
                return
            
            # 轉換為DataFrame
            columns = ["序號", "餐廳編號", "餐廳名稱", "餐點編號", "菜牌編號", 
                      "餐點名稱", "英文名稱", "建檔日期"]
            df = pd.DataFrame(results, columns=columns)
            
            # 儲存為Excel
            df.to_excel(file_path, index=False)
            
            messagebox.showinfo("成功", f"資料已成功下載至：\n{file_path}")

        except Exception as e:
            messagebox.showerror("錯誤", f"下載資料時發生錯誤：\n{str(e)}")
        finally:
            self.db.close_connection()
