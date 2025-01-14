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
            # 先檢查是否有���複
            check_query = """
            SELECT 菜牌編號, COUNT(*) as count
            FROM menu_items
            GROUP BY 菜牌編號
            HAVING COUNT(*) > 1
            """
            self.db.cursor.execute(check_query)
            duplicates = self.db.cursor.fetchall()

            if not duplicates:
                messagebox.showinfo("提示", "資料庫中沒有重複的菜牌編號")
                return

            # 詢問用戶是否要刪除
            if not messagebox.askyesno("確認", 
                f"發現 {len(duplicates)} 個重複的菜牌編號，是否要刪除重複項目？\n" +
                "（將保留每個編號的第一筆資料）"):
                return

            # 刪除重複項目（保留最早的一筆）
            delete_query = """
            DELETE m1 FROM menu_items m1
            INNER JOIN menu_items m2
            WHERE m1.菜牌編號 = m2.菜牌編號
            AND m1.序號 > m2.序號
            """
            self.db.cursor.execute(delete_query)
            self.db.connection.commit()

            messagebox.showinfo("成功", "已成功刪除重複的菜牌編號")

        except Exception as e:
            messagebox.showerror("錯誤", f"刪除重複時發生錯誤：\n{str(e)}")
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
