// 全域 JavaScript 功能

// 文檔載入完成後執行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化檔案上傳功能
    initializeFileUploads();
    
    // 初始化表單驗證
    initializeFormValidation();
    
    // 自動隱藏提示訊息
    autoHideAlerts();
    
    // 添加載入動畫
    addLoadingAnimations();
});

// 初始化 Bootstrap 工具提示
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化檔案上傳功能
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const files = e.target.files;
            const maxSize = 50 * 1024 * 1024; // 50MB
            let totalSize = 0;
            
            // 檢查檔案大小
            for (let file of files) {
                totalSize += file.size;
                if (file.size > maxSize) {
                    showAlert('檔案 "' + file.name + '" 太大，請選擇小於 50MB 的檔案。', 'danger');
                    e.target.value = '';
                    return;
                }
            }
            
            if (totalSize > maxSize * 2) {
                showAlert('總檔案大小太大，請減少檔案數量或選擇較小的檔案。', 'warning');
                e.target.value = '';
                return;
            }
            
            // 更新檔案選擇提示
            updateFileSelectionText(input, files.length);
        });
        
        // 拖放功能
        input.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('drag-over');
        });
        
        input.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('drag-over');
        });
        
        input.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            this.files = files;
            
            // 觸發 change 事件
            const event = new Event('change', { bubbles: true });
            this.dispatchEvent(event);
        });
    });
}

// 更新檔案選擇文字
function updateFileSelectionText(input, fileCount) {
    const formText = input.parentNode.querySelector('.form-text');
    if (formText && fileCount > 0) {
        const originalText = formText.textContent;
        if (input.multiple) {
            formText.textContent = `已選擇 ${fileCount} 個檔案`;
        } else {
            formText.textContent = '已選擇檔案';
        }
        
        // 3秒後恢復原始文字
        setTimeout(() => {
            formText.textContent = originalText;
        }, 3000);
    }
}

// 初始化表單驗證
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                showAlert('請填寫所有必填欄位並確保格式正確。', 'warning');
            }
            
            form.classList.add('was-validated');
        });
        
        // 即時驗證
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
}

// 自動隱藏提示訊息
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        // 成功訊息 3 秒後自動隱藏
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                fadeOutAlert(alert);
            }, 3000);
        }
        // 錯誤訊息 8 秒後自動隱藏
        else if (alert.classList.contains('alert-danger')) {
            setTimeout(() => {
                fadeOutAlert(alert);
            }, 8000);
        }
        // 警告訊息 5 秒後自動隱藏
        else if (alert.classList.contains('alert-warning')) {
            setTimeout(() => {
                fadeOutAlert(alert);
            }, 5000);
        }
    });
}

// 淡出提示訊息
function fadeOutAlert(alert) {
    alert.style.transition = 'opacity 0.5s ease';
    alert.style.opacity = '0';
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 500);
}

// 顯示自定義提示訊息
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        const alertDiv = document.createElement('div');
        alertDiv.innerHTML = alertHtml;
        container.insertBefore(alertDiv.firstElementChild, container.firstElementChild);
        
        // 自動隱藏
        setTimeout(() => {
            const newAlert = container.querySelector('.alert');
            if (newAlert) {
                fadeOutAlert(newAlert);
            }
        }, type === 'danger' ? 8000 : 5000);
    }
}

// 獲取提示訊息圖標
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 添加載入動畫
function addLoadingAnimations() {
    // 為所有提交按鈕添加載入狀態
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    
    submitButtons.forEach(button => {
        const form = button.closest('form');
        if (form && !form.hasAttribute('data-no-loading')) {
            form.addEventListener('submit', function() {
                if (form.checkValidity()) {
                    showButtonLoading(button);
                }
            });
        }
    });
}

// 顯示按鈕載入狀態
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    const loadingText = button.getAttribute('data-loading-text') || 
                       '<i class="fas fa-spinner fa-spin me-1"></i>處理中...';
    
    button.innerHTML = loadingText;
    button.disabled = true;
    
    // 儲存原始文字以便恢復
    button.setAttribute('data-original-text', originalText);
}

// 恢復按鈕原始狀態
function restoreButtonState(button) {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.innerHTML = originalText;
        button.disabled = false;
        button.removeAttribute('data-original-text');
    }
}

// 顯示確認對話框
function showConfirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 格式化檔案大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 日期格式驗證
function validateDateFormat(dateString) {
    const singleDatePattern = /^\d{8}$/;
    const rangeDatePattern = /^\d{8}-\d{8}$/;
    
    return singleDatePattern.test(dateString) || rangeDatePattern.test(dateString);
}

// 工具函數：複製到剪貼簿
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('已複製到剪貼簿', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// 備用複製方法
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('已複製到剪貼簿', 'success');
    } catch (err) {
        showAlert('複製失敗，請手動複製', 'error');
    }
    
    document.body.removeChild(textArea);
}

// 全域錯誤處理
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showAlert('發生未預期的錯誤，請重新載入頁面或聯繫管理員。', 'danger');
});

// 網路錯誤處理
window.addEventListener('online', function() {
    showAlert('網路連線已恢復', 'success');
});

window.addEventListener('offline', function() {
    showAlert('網路連線中斷，請檢查您的網路設定', 'warning');
});

// 導出全域函數
window.showAlert = showAlert;
window.showConfirmDialog = showConfirmDialog;
window.copyToClipboard = copyToClipboard;
window.validateDateFormat = validateDateFormat;
window.formatFileSize = formatFileSize;
