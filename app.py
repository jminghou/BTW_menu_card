from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import json

# 導入原有的模組功能
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

app = Flask(__name__)
app.secret_key = 'mediatek_menu_card_secret_key_2024'

# 設定檔案上傳
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv'}

# 確保上傳資料夾存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/clean_excel', methods=['GET', 'POST'])
def clean_excel():
    """資料清洗功能"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                # 呼叫清洗功能，但需要修改以適應 Flask
                result = clean_excel_file_web(file_path)
                if result['success']:
                    flash(f'檔案清洗完成：{result["new_file_path"]}', 'success')
                    return send_file(result['new_file_path'], as_attachment=True)
                else:
                    flash(f'檔案清洗失敗：{result["error"]}', 'error')
            except Exception as e:
                flash(f'處理過程中發生錯誤：{str(e)}', 'error')
            finally:
                # 清理上傳的檔案
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('不支援的檔案格式', 'error')
    
    return render_template('clean_excel.html')

@app.route('/generate_menu_codes', methods=['GET', 'POST'])
def generate_menu_codes():
    """菜牌編號產生功能"""
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        success_files = []
        error_files = []
        result_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                try:
                    new_file_path, error = process_menu_codes(file_path)
                    
                    if error:
                        error_files.append(f"{filename}: {error}")
                    else:
                        success_files.append(new_file_path)
                        result_files.append({
                            'original': filename,
                            'processed': os.path.basename(new_file_path),
                            'path': new_file_path
                        })
                except Exception as e:
                    error_files.append(f"{filename}: {str(e)}")
                finally:
                    # 清理上傳的檔案
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        if success_files:
            flash(f'成功處理 {len(success_files)} 個檔案', 'success')
            return render_template('generate_menu_codes.html', result_files=result_files)
        else:
            if error_files:
                flash('處理失敗：' + '; '.join(error_files), 'error')
            else:
                flash('沒有成功處理任何檔案', 'error')
    
    return render_template('generate_menu_codes.html')

@app.route('/upload_database', methods=['GET', 'POST'])
def upload_database():
    """上傳資料庫功能"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                uploader = DatabaseUploader()
                result = uploader.upload_file(file_path)
                if result:
                    flash('檔案上傳資料庫成功', 'success')
                else:
                    flash('檔案上傳資料庫失敗', 'error')
            except Exception as e:
                flash(f'上傳過程中發生錯誤：{str(e)}', 'error')
            finally:
                # 清理上傳的檔案
                if os.path.exists(file_path):
                    os.remove(file_path)
                uploader.close_connection()
        else:
            flash('不支援的檔案格式', 'error')
    
    return render_template('upload_database.html')

@app.route('/download_no_english')
def download_no_english():
    """下載無英文菜單"""
    try:
        from module.web_functions import download_no_english_menus_web
        file_path = download_no_english_menus_web()
        if file_path:
            return send_file(file_path, as_attachment=True)
        else:
            flash('下載失敗', 'error')
    except Exception as e:
        flash(f'下載過程中發生錯誤：{str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/upload_english', methods=['GET', 'POST'])
def upload_english():
    """上傳菜單英文名稱"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                from module.web_functions import upload_english_names_web
                result = upload_english_names_web(file_path)
                if result:
                    flash('英文名稱上傳成功', 'success')
                else:
                    flash('英文名稱上傳失敗', 'error')
            except Exception as e:
                flash(f'上傳過程中發生錯誤：{str(e)}', 'error')
            finally:
                # 清理上傳的檔案
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('請選擇 CSV 檔案', 'error')
    
    return render_template('upload_english.html')

@app.route('/database_functions')
def database_functions():
    """資料庫功能頁面"""
    return render_template('database_functions.html')

@app.route('/remove_duplicates', methods=['POST'])
def remove_duplicates():
    """刪除重複菜牌編號"""
    try:
        db_function = DatabaseFunction()
        result = db_function.remove_duplicates()
        db_function.db.close_connection()
        return jsonify({'success': True, 'message': '重複資料刪除完成'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'刪除過程中發生錯誤：{str(e)}'})

@app.route('/download_all')
def download_all():
    """下載所有菜牌"""
    try:
        from module.web_functions import download_all_web
        file_path = download_all_web()
        if file_path:
            return send_file(file_path, as_attachment=True)
        else:
            flash('下載失敗', 'error')
    except Exception as e:
        flash(f'下載過程中發生錯誤：{str(e)}', 'error')
    
    return redirect(url_for('database_functions'))

@app.route('/new_menu_restaurant', methods=['GET', 'POST'])
def new_menu_restaurant():
    """新菜牌/新餐廳功能"""
    if request.method == 'POST':
        action = request.form.get('action')
        date_range = request.form.get('date_range', '').strip()
        
        if not date_range or date_range == "YYYYMMDD-YYYYMMDD或YYYYMMDD":
            flash('請輸入日期區間，格式為 YYYYMMDD-YYYYMMDD 或單一日期 YYYYMMDD', 'error')
            return redirect(request.url)
        
        try:
            if action == 'new_menu':
                from module.web_functions import export_new_menus_web
                file_path = export_new_menus_web(date_range)
                if file_path:
                    return send_file(file_path, as_attachment=True)
                else:
                    flash('新菜牌導出失敗', 'error')
            elif action == 'new_restaurant':
                from module.web_functions import export_new_restaurants_web
                file_path = export_new_restaurants_web(date_range)
                if file_path:
                    return send_file(file_path, as_attachment=True)
                else:
                    flash('新餐廳導出失敗', 'error')
        except Exception as e:
            flash(f'導出過程中發生錯誤：{str(e)}', 'error')
    
    return render_template('new_menu_restaurant.html')

@app.route('/convert_csv', methods=['GET', 'POST'])
def convert_csv():
    """轉換CSV到TXT功能"""
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('沒有選擇檔案', 'error')
            return redirect(request.url)
        
        file_paths = []
        for file in files:
            if file and file.filename.endswith('.csv'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        if file_paths:
            try:
                from module.web_functions import convert_csv_to_unicode_txt_web
                result_files = convert_csv_to_unicode_txt_web(file_paths)
                flash(f'成功轉換 {len(result_files)} 個檔案', 'success')
                # 可以返回轉換後的檔案供下載
                return render_template('convert_csv.html', result_files=result_files)
            except Exception as e:
                flash(f'轉換過程中發生錯誤：{str(e)}', 'error')
            finally:
                # 清理上傳的檔案
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        os.remove(file_path)
        else:
            flash('請選擇 CSV 檔案', 'error')
    
    return render_template('convert_csv.html')

@app.route('/download_file/<path:filename>')
def download_file(filename):
    """下載生成的檔案"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(f'下載檔案失敗：{str(e)}', 'error')
        return redirect(url_for('index'))

# 需要為 web 版本改寫的函數
def clean_excel_file_web(file_path):
    """Web 版本的資料清洗功能"""
    try:
        # 這裡需要改寫原有的 clean_excel_file 函數以適應 web 版本
        # 目前先返回一個基本實現
        import pandas as pd
        from module.mod_number import generate_menu_code, convert_to_code
        
        # 讀取Excel文件
        df = pd.read_excel(file_path)
        
        # 尋找並刪除"售價"
        price_columns = [col for col in df.columns if "售價" in col]
        if price_columns:
            df = df.drop(columns=price_columns)
        
        # 處理日期欄位
        date_columns = [col for col in df.columns if "日期" in col]
        for date_col in date_columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%m/%d')
            except:
                continue
        
        # 處理據點欄位
        location_columns = [col for col in df.columns if "據點" in col]
        for loc_col in location_columns:
            try:
                df[loc_col] = df[loc_col].str.replace('-內部', '', regex=False)
            except:
                continue
        
        # 生成新檔案路徑
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_cleaned_{timestamp}.xlsx")
        
        # 儲存新檔案
        df.to_excel(new_file_path, index=False)
        
        return {'success': True, 'new_file_path': new_file_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
