// Enhanced Form validation and UI interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all features
    initAlerts();
    initFormValidation();
    initCharacterCounters();
    initStatusConfirmation();
    initTableInteractions();
    initAnimations();
    initPasswordToggle();
    initFileUpload();
    initTooltips();
    initSmoothScroll();
});

// Auto-hide alerts with animation
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach((alert, index) => {
        // Stagger animation
        alert.style.animationDelay = `${index * 0.1}s`;
        
        // Add close button
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = 'float: right; cursor: pointer; font-size: 1.5rem; line-height: 1; margin-left: 10px;';
        closeBtn.onclick = () => dismissAlert(alert);
        alert.insertBefore(closeBtn, alert.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => dismissAlert(alert), 5000);
    });
}

function dismissAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    alert.style.transition = 'all 0.5s ease';
    setTimeout(() => alert.remove(), 500);
}

// Enhanced form validation with real-time feedback
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        // Real-time validation
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('error')) {
                    validateField(this);
                }
            });
        });
        
        // Form submission
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!validateField(field)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields correctly', 'error');
                
                // Scroll to first error
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            } else {
                // Show loading state
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="loading"></span> Processing...';
                }
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Remove previous error
    removeFieldError(field);
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Password validation
    if (field.type === 'password' && value && field.name === 'password') {
        if (value.length < 6) {
            isValid = false;
            errorMessage = 'Password must be at least 6 characters';
        }
    }
    
    // Confirm password validation
    if (field.name === 'confirm_password' && value) {
        const password = document.querySelector('input[name="password"]');
        if (password && value !== password.value) {
            isValid = false;
            errorMessage = 'Passwords do not match';
        }
    }
    
    // Number validation
    if (field.type === 'number' && value) {
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        const num = parseFloat(value);
        
        if (min && num < parseFloat(min)) {
            isValid = false;
            errorMessage = `Value must be at least ${min}`;
        }
        if (max && num > parseFloat(max)) {
            isValid = false;
            errorMessage = `Value must not exceed ${max}`;
        }
    }
    
    if (!isValid) {
        showFieldError(field, errorMessage);
    } else {
        field.classList.add('valid');
    }
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('error');
    field.classList.remove('valid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = 'color: #ef4444; font-size: 0.85rem; margin-top: 5px; animation: fadeIn 0.3s;';
    
    field.parentNode.appendChild(errorDiv);
}

function removeFieldError(field) {
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Character counter with visual feedback
function initCharacterCounters() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength') || 500;
        
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.style.cssText = 'text-align: right; font-size: 0.85rem; margin-top: 5px; transition: color 0.3s;';
        
        textarea.parentNode.appendChild(counter);
        
        const updateCounter = () => {
            const remaining = maxLength - textarea.value.length;
            const percentage = (textarea.value.length / maxLength) * 100;
            
            counter.textContent = `${remaining} characters remaining`;
            
            if (percentage > 90) {
                counter.style.color = '#ef4444';
            } else if (percentage > 75) {
                counter.style.color = '#f59e0b';
            } else {
                counter.style.color = '#64748b';
            }
        };
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
}

// Confirmation dialogs with custom styling
function initStatusConfirmation() {
    const statusSelects = document.querySelectorAll('select[name="status"]');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            if (this.value === 'Rejected') {
                if (!confirm('⚠️ Are you sure you want to reject this complaint?\n\nThis action will notify the student.')) {
                    this.value = 'Pending Review';
                }
            }
        });
    });
}

// Enhanced table interactions
function initTableInteractions() {
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach((row, index) => {
        // Stagger animation
        row.style.animation = `fadeInUp 0.4s ease-out ${index * 0.05}s both`;
        
        row.addEventListener('click', function() {
            tableRows.forEach(r => {
                r.style.backgroundColor = '';
                r.classList.remove('selected');
            });
            this.style.backgroundColor = '#f0f8ff';
            this.classList.add('selected');
        });
        
        row.addEventListener('mouseenter', function() {
            if (!this.classList.contains('selected')) {
                this.style.backgroundColor = '#f8fafc';
            }
        });
        
        row.addEventListener('mouseleave', function() {
            if (!this.classList.contains('selected')) {
                this.style.backgroundColor = '';
            }
        });
    });
}

// Scroll animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    const animatedElements = document.querySelectorAll('.stat-card, .complaint-card, .exam-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Password visibility toggle
function initPasswordToggle() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.innerHTML = '👁️';
        toggleBtn.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1.2rem; opacity: 0.6; transition: opacity 0.3s;';
        
        toggleBtn.addEventListener('mouseenter', () => toggleBtn.style.opacity = '1');
        toggleBtn.addEventListener('mouseleave', () => toggleBtn.style.opacity = '0.6');
        
        toggleBtn.addEventListener('click', function() {
            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '🙈';
            } else {
                input.type = 'password';
                this.innerHTML = '👁️';
            }
        });
        
        wrapper.appendChild(toggleBtn);
    });
}

// File upload preview
function initFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            if (fileName) {
                let label = this.parentNode.querySelector('.file-label');
                if (!label) {
                    label = document.createElement('div');
                    label.className = 'file-label';
                    label.style.cssText = 'margin-top: 10px; padding: 10px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; color: #166534; font-size: 0.9rem;';
                    this.parentNode.appendChild(label);
                }
                label.innerHTML = `✅ Selected: <strong>${fileName}</strong>`;
            }
        });
    });
}

// Tooltips
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(el => {
        el.style.position = 'relative';
        el.style.cursor = 'help';
        
        el.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = 'position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: #1e293b; color: white; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; white-space: nowrap; z-index: 1000; animation: fadeIn 0.3s;';
            
            this.appendChild(tooltip);
        });
        
        el.addEventListener('mouseleave', function() {
            const tooltip = this.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}

// Smooth scroll for anchor links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'all 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}


// Scroll to Top Button
function initScrollToTop() {
    // Create button if it doesn't exist
    let scrollBtn = document.querySelector('.scroll-to-top');
    if (!scrollBtn) {
        scrollBtn = document.createElement('button');
        scrollBtn.className = 'scroll-to-top';
        scrollBtn.innerHTML = '↑';
        scrollBtn.setAttribute('aria-label', 'Scroll to top');
        document.body.appendChild(scrollBtn);
    }
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollBtn.classList.add('show');
        } else {
            scrollBtn.classList.remove('show');
        }
    });
    
    // Scroll to top on click
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize scroll to top after DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollToTop);
} else {
    initScrollToTop();
}

// Add loading state to forms
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.tagName === 'FORM') {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML || submitBtn.value;
            submitBtn.disabled = true;
            
            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.innerHTML = '<span class="loading"></span> Processing...';
            }
            
            // Re-enable after 5 seconds as fallback
            setTimeout(() => {
                submitBtn.disabled = false;
                if (submitBtn.tagName === 'BUTTON') {
                    submitBtn.innerHTML = originalText;
                }
            }, 5000);
        }
    }
});

// Add ripple effect to buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
            animation: ripple 0.6s ease-out;
        `;
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
});

// Add CSS for ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        from {
            transform: scale(0);
            opacity: 1;
        }
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Auto-save form data to localStorage (optional feature)
function initAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    forms.forEach(form => {
        const formId = form.id || 'form-' + Math.random().toString(36).substr(2, 9);
        
        // Load saved data
        const savedData = localStorage.getItem('form-' + formId);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field && field.type !== 'password') {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.error('Error loading saved form data:', e);
            }
        }
        
        // Save on input
        form.addEventListener('input', debounce(function() {
            const formData = {};
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.name && input.type !== 'password') {
                    formData[input.name] = input.value;
                }
            });
            localStorage.setItem('form-' + formId, JSON.stringify(formData));
        }, 500));
        
        // Clear on submit
        form.addEventListener('submit', function() {
            localStorage.removeItem('form-' + formId);
        });
    });
}

// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search (if exists)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals or clear focus
    if (e.key === 'Escape') {
        document.activeElement.blur();
    }
});

// Add copy to clipboard functionality
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }
}

// Lazy load images (if any)
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}

// Performance monitoring (optional)
if (window.performance && window.performance.timing) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log('Page load time:', pageLoadTime + 'ms');
        }, 0);
    });
}

// Add confirmation for destructive actions
document.querySelectorAll('[data-confirm]').forEach(element => {
    element.addEventListener('click', function(e) {
        const message = this.getAttribute('data-confirm');
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });
});

// Initialize all features when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initAutoSave();
    });
} else {
    initAutoSave();
}

console.log('✨ Smart Grievance System - Enhanced UI Loaded');
