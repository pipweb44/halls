// Main JavaScript for Hall Booking System

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Hall availability checker
    const availabilityForm = document.getElementById('availability-form');
    if (availabilityForm) {
        availabilityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            checkAvailability();
        });
    }

    // Booking form enhancement
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        const startDateTime = document.getElementById('id_start_datetime');
        const endDateTime = document.getElementById('id_end_datetime');
        const attendeesCount = document.getElementById('id_attendees_count');
        const hallCapacity = document.getElementById('hall-capacity');

        if (startDateTime && endDateTime) {
            startDateTime.addEventListener('change', function() {
                // Set minimum end time to start time + 1 hour
                const startDate = new Date(this.value);
                const minEndDate = new Date(startDate.getTime() + 60 * 60 * 1000);
                endDateTime.min = minEndDate.toISOString().slice(0, 16);
                
                // Auto-calculate duration and price
                calculatePrice();
            });

            endDateTime.addEventListener('change', function() {
                calculatePrice();
            });
        }

        if (attendeesCount && hallCapacity) {
            attendeesCount.addEventListener('input', function() {
                const capacity = parseInt(hallCapacity.value);
                const attendees = parseInt(this.value);
                
                if (attendees > capacity) {
                    this.setCustomValidity(`عدد الحضور لا يمكن أن يتجاوز سعة القاعة (${capacity})`);
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }

    // Search functionality
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500);
        });
    }

    // Category filter
    const categorySelect = document.getElementById('category');
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            this.form.submit();
        });
    }

    // Image preview for file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.style.maxWidth = '200px';
                    preview.style.maxHeight = '200px';
                    preview.className = 'mt-2';
                    
                    const container = input.parentElement;
                    const existingPreview = container.querySelector('img');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    container.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Loading spinner
    function showLoading(element) {
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        spinner.id = 'loading-spinner';
        element.appendChild(spinner);
        element.disabled = true;
    }

    function hideLoading(element) {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.remove();
        }
        element.disabled = false;
    }

    // Check availability function
    function checkAvailability() {
        const form = document.getElementById('availability-form');
        const submitBtn = form.querySelector('button[type="submit"]');
        const hallId = form.querySelector('input[name="hall_id"]').value;
        const startDateTime = form.querySelector('input[name="start_datetime"]').value;
        const endDateTime = form.querySelector('input[name="end_datetime"]').value;

        if (!startDateTime || !endDateTime) {
            showAlert('يرجى تحديد تاريخ ووقت البداية والنهاية', 'warning');
            return;
        }

        showLoading(submitBtn);

        fetch('/api/check-availability/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                hall_id: hallId,
                start_datetime: startDateTime,
                end_datetime: endDateTime
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(submitBtn);
            if (data.available) {
                showAlert(data.message, 'success');
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            hideLoading(submitBtn);
            showAlert('حدث خطأ في التحقق من التوفر', 'danger');
            console.error('Error:', error);
        });
    }

    // Calculate price function
    function calculatePrice() {
        const startDateTime = document.getElementById('id_start_datetime');
        const endDateTime = document.getElementById('id_end_datetime');
        const pricePerHour = document.getElementById('price-per-hour');
        const totalPriceElement = document.getElementById('total-price');

        if (startDateTime && endDateTime && pricePerHour && totalPriceElement) {
            const start = new Date(startDateTime.value);
            const end = new Date(endDateTime.value);
            
            if (start && end && start < end) {
                const durationHours = (end - start) / (1000 * 60 * 60);
                const pricePerHourValue = parseFloat(pricePerHour.value);
                const totalPrice = durationHours * pricePerHourValue;
                
                totalPriceElement.textContent = totalPrice.toFixed(2);
                totalPriceElement.style.display = 'block';
            }
        }
    }

    // Show alert function
    function showAlert(message, type) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertContainer, container.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertContainer);
            bsAlert.close();
        }, 5000);
    }

    // Get CSRF token function
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);

    // Observe all cards and sections
    document.querySelectorAll('.card, section').forEach(el => {
        observer.observe(el);
    });

    // Mobile menu enhancement
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking on a link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                    bsCollapse.hide();
                }
            });
        });
    }

    // Back to top button
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.className = 'btn btn-primary position-fixed';
    backToTopBtn.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px; display: none;';
    document.body.appendChild(backToTopBtn);

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Print functionality for booking details
    const printBtn = document.querySelector('.print-btn');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // Share functionality
    const shareBtn = document.querySelector('.share-btn');
    if (shareBtn && navigator.share) {
        shareBtn.addEventListener('click', async () => {
            try {
                await navigator.share({
                    title: document.title,
                    url: window.location.href
                });
            } catch (err) {
                console.log('Error sharing:', err);
            }
        });
    }

    // Initialize any additional plugins or features
    console.log('Hall Booking System initialized successfully!');
}); 