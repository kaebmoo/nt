// anomaly_web/static/js/main.js
// Main JavaScript for Anomaly Detection System

$(document).ready(function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').not('.alert-permanent').fadeOut('slow');
    }, 5000);

    // Confirm delete actions
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('คุณแน่ใจหรือไม่ที่จะลบรายการนี้?')) {
            e.preventDefault();
            return false;
        }
    });

    // Number formatting
    function formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        return num.toLocaleString('th-TH');
    }

    // Date formatting
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('th-TH', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // File size formatting
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Drag and drop for file upload
    const dropZone = document.getElementById('fileDropZone');
    if (dropZone) {
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
                // Trigger file name display
                displayFileName(files[0]);
            }
        });
    }

    // Display selected file name
    function displayFileName(file) {
        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-file-earmark"></i> <strong>${file.name}</strong><br>
                    <small>ขนาด: ${formatFileSize(file.size)} | ประเภท: ${file.type}</small>
                </div>
            `;
        }
    }

    // File input change event
    $('#fileInput').on('change', function() {
        const file = this.files[0];
        if (file) {
            displayFileName(file);
        }
    });

    // Form validation
    $('form').on('submit', function() {
        const form = $(this);
        const requiredFields = form.find('[required]');
        let isValid = true;

        requiredFields.each(function() {
            const field = $(this);
            if (!field.val()) {
                field.addClass('is-invalid');
                isValid = false;
            } else {
                field.removeClass('is-invalid');
            }
        });

        if (!isValid) {
            alert('กรุณากรอกข้อมูลให้ครบถ้วน');
            return false;
        }
    });

    // Clear invalid state on input
    $('.form-control, .form-select').on('input change', function() {
        $(this).removeClass('is-invalid');
    });

    // Multi-select helper text
    $('select[multiple]').after(`
        <small class="text-muted">
            <i class="bi bi-info-circle"></i> กด Ctrl (Windows) หรือ Cmd (Mac) เพื่อเลือกหลายรายการ
        </small>
    `);

    // Table search functionality
    $('#tableSearch').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        $('#dataTable tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Export table to CSV
    window.exportTableToCSV = function(tableId, filename) {
        const table = document.getElementById(tableId);
        let csv = [];
        
        // Headers
        const headers = [];
        table.querySelectorAll('thead th').forEach(th => {
            headers.push(th.textContent.trim());
        });
        csv.push(headers.join(','));
        
        // Rows
        table.querySelectorAll('tbody tr').forEach(row => {
            const rowData = [];
            row.querySelectorAll('td').forEach(td => {
                rowData.push('"' + td.textContent.trim().replace(/"/g, '""') + '"');
            });
            csv.push(rowData.join(','));
        });
        
        // Download
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename || 'export.csv';
        link.click();
    };

    // Copy to clipboard
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('คัดลอกแล้ว!', 'success');
        }, function() {
            showToast('ไม่สามารถคัดลอกได้', 'error');
        });
    };

    // Show toast notification
    window.showToast = function(message, type = 'info') {
        const toastHTML = `
            <div class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        const toastContainer = $('#toastContainer');
        if (toastContainer.length === 0) {
            $('body').append('<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }
        
        $('#toastContainer').append(toastHTML);
        const toastElement = $('.toast').last()[0];
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            $(toastElement).remove();
        });
    };

    // Loading overlay
    window.showLoading = function(message = 'กำลังโหลด...') {
        const loadingHTML = `
            <div id="loadingOverlay" class="modal d-block" style="background-color: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content text-center p-4">
                        <div class="spinner-border text-primary mx-auto mb-3" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <h5>${message}</h5>
                    </div>
                </div>
            </div>
        `;
        $('body').append(loadingHTML);
    };

    window.hideLoading = function() {
        $('#loadingOverlay').remove();
    };

    console.log('Anomaly Detection System - Initialized');
});
