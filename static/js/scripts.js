// Main JavaScript for Carbon ESG Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Real-time calculation preview for individual form
    const individualForm = document.getElementById('individualForm');
    if (individualForm) {
        const inputs = individualForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', updateCarbonPreview);
        });
    }

    // Auto-format numbers with commas
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                const num = parseFloat(this.value);
                if (!isNaN(num)) {
                    this.value = num.toLocaleString();
                }
            }
        });
        
        input.addEventListener('focus', function() {
            this.value = this.value.replace(/,/g, '');
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Print report button functionality
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.btn-copy');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Show success feedback
                    const originalHTML = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    this.classList.add('btn-success');
                    this.classList.remove('btn-outline-secondary');
                    
                    setTimeout(() => {
                        this.innerHTML = originalHTML;
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-secondary');
                    }, 2000);
                });
            }
        });
    });

    // Chart color schemes
    window.chartColors = {
        green: '#2E7D32',
        lightGreen: '#4CAF50',
        blue: '#2196F3',
        yellow: '#FFC107',
        orange: '#FF9800',
        red: '#F44336',
        purple: '#9C27B0',
        teal: '#009688'
    };
});

// Carbon preview calculation function
function updateCarbonPreview() {
    // This is a simplified preview - actual calculation is done server-side
    const form = document.getElementById('individualForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const previewElement = document.getElementById('carbonPreview');
    
    if (previewElement) {
        // Show loading state
        previewElement.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Calculating...';
        
        // Simulate calculation (in real app, this would be an API call)
        setTimeout(() => {
            const electricity = parseFloat(formData.get('electricity_kwh')) || 300;
            const vehicleType = formData.get('vehicle_type');
            const vehicleKm = parseFloat(formData.get('vehicle_km')) || 0;
            
            // Simple estimation
            let estimate = electricity * 0.5 * 12; // Electricity
            
            if (vehicleType && vehicleType !== 'none') {
                const factor = vehicleType === 'petrol' ? 0.18 : 0.21;
                estimate += vehicleKm * factor * 12;
            }
            
            // Add base for other factors
            estimate += 2000; // Base for diet, shopping, etc
            
            previewElement.innerHTML = `
                <div class="text-success">
                    <i class="bi bi-tree"></i> Estimated: ${Math.round(estimate).toLocaleString()} kg CO2e/year
                </div>
                <small class="text-muted">This is a rough estimate. Complete form for accurate calculation.</small>
            `;
        }, 500);
    }
}

// File upload preview
function previewFile(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('filePreview');
            if (preview) {
                preview.innerHTML = `
                    <div class="alert alert-info">
                        <i class="bi bi-file-earmark-text"></i> Selected: ${input.files[0].name}
                        <br><small>Size: ${(input.files[0].size / 1024).toFixed(2)} KB</small>
                    </div>
                `;
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Export data functionality
function exportData(format) {
    const data = {
        timestamp: new Date().toISOString(),
        user: document.querySelector('.user-info')?.innerText || 'Unknown',
        // Add more data as needed
    };
    
    let content, mimeType, filename;
    
    if (format === 'json') {
        content = JSON.stringify(data, null, 2);
        mimeType = 'application/json';
        filename = `carbon_esg_data_${Date.now()}.json`;
    } else if (format === 'csv') {
        // Simple CSV conversion
        content = 'Category,Value\n';
        Object.entries(data).forEach(([key, value]) => {
            content += `${key},${value}\n`;
        });
        mimeType = 'text/csv';
        filename = `carbon_esg_data_${Date.now()}.csv`;
    }
    
    // Download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Theme toggle (light/dark mode)
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-bs-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    body.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update button icon
    const themeButton = document.getElementById('themeToggle');
    if (themeButton) {
        themeButton.innerHTML = newTheme === 'light' 
            ? '<i class="bi bi-moon"></i>' 
            : '<i class="bi bi-sun"></i>';
    }
}

// Initialize theme from localStorage
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-bs-theme', savedTheme);
    
    const themeButton = document.getElementById('themeToggle');
    if (themeButton) {
        themeButton.innerHTML = savedTheme === 'light' 
            ? '<i class="bi bi-moon"></i>' 
            : '<i class="bi bi-sun"></i>';
    }
}

// Initialize when page loads
initTheme();