// Main JavaScript file for Driving School Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Notification mark as read functionality
    const notificationLinks = document.querySelectorAll('.mark-notification-read');
    notificationLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.notificationId;
            
            fetch(`/notification/read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (response.ok) {
                    this.closest('.notification-item').style.opacity = '0.5';
                    this.textContent = 'Read';
                    this.classList.remove('btn-outline-primary');
                    this.classList.add('btn-outline-secondary');
                    this.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    // Lesson booking form enhancements
    const lessonForm = document.getElementById('lesson-booking-form');
    if (lessonForm) {
        const dateInput = lessonForm.querySelector('input[type="date"]');
        const startTimeInput = lessonForm.querySelector('input[name="start_time"]');
        const endTimeInput = lessonForm.querySelector('input[name="end_time"]');

        // Set minimum date to today
        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.min = today;
        }

        // Auto-calculate end time when start time changes
        if (startTimeInput && endTimeInput) {
            startTimeInput.addEventListener('change', function() {
                if (this.value) {
                    const startTime = new Date(`2000-01-01T${this.value}`);
                    const endTime = new Date(startTime.getTime() + 60 * 60 * 1000); // Add 1 hour
                    endTimeInput.value = endTime.toTimeString().slice(0, 5);
                }
            });
        }
    }

    // Dashboard stats animation
    const statsNumbers = document.querySelectorAll('.stats-number');
    statsNumbers.forEach(function(stat) {
        const finalValue = parseInt(stat.textContent);
        let currentValue = 0;
        const increment = finalValue / 50;
        
        const timer = setInterval(function() {
            currentValue += increment;
            if (currentValue >= finalValue) {
                stat.textContent = finalValue;
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(currentValue);
            }
        }, 20);
    });
});

// Helper function to get CSRF token
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

// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.body.setAttribute('data-theme', savedTheme);
