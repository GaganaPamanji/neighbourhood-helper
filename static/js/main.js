// Main JavaScript file for the Neighbourhood Assistance Program

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Task category selection
    const categorySelect = document.getElementById('category');
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            updateCategoryHelp(this.value);
        });
        
        // Initialize with current value
        if (categorySelect.value) {
            updateCategoryHelp(categorySelect.value);
        }
    }
    
    // Task status filters
    const statusFilters = document.querySelectorAll('.status-filter');
    if (statusFilters.length > 0) {
        statusFilters.forEach(filter => {
            filter.addEventListener('click', function(e) {
                e.preventDefault();
                const status = this.getAttribute('data-status');
                filterTasksByStatus(status);
                
                // Update active class
                statusFilters.forEach(f => f.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
    
    // Rating input
    const ratingInputs = document.querySelectorAll('input[name="rating"]');
    if (ratingInputs.length > 0) {
        ratingInputs.forEach(input => {
            input.addEventListener('change', function() {
                updateRatingStars(this.value);
            });
        });
    }
    
    // Task completion confirmation
    const completeTaskBtn = document.getElementById('complete-task-btn');
    if (completeTaskBtn) {
        completeTaskBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to mark this task as complete?')) {
                e.preventDefault();
            }
        });
    }
    
    // Volunteer confirmation
    const volunteerBtn = document.getElementById('volunteer-btn');
    if (volunteerBtn) {
        volunteerBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to volunteer for this task?')) {
                e.preventDefault();
            }
        });
    }
});

// Helper functions
function updateCategoryHelp(category) {
    const helpText = document.getElementById('category-help');
    if (!helpText) return;
    
    const helpMessages = {
        'household': 'Includes light cleaning, laundry, organizing, etc.',
        'errands': 'Grocery shopping, picking up prescriptions, post office trips, etc.',
        'companionship': 'Friendly visits or phone calls to reduce loneliness',
        'outdoor': 'Lawn care, snow shoveling, minor repairs, etc.',
        'technology': 'Basic computer skills, troubleshooting devices, etc.',
        'childcare': 'Occasional babysitting, homework help, etc.',
        'other': 'Any other type of assistance not covered in other categories'
    };
    
    helpText.textContent = helpMessages[category] || '';
}

function filterTasksByStatus(status) {
    const taskCards = document.querySelectorAll('.task-card');
    if (taskCards.length === 0) return;
    
    if (status === 'all') {
        taskCards.forEach(card => {
            card.style.display = 'block';
        });
    } else {
        taskCards.forEach(card => {
            if (card.getAttribute('data-status') === status) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
}

function updateRatingStars(rating) {
    const starsContainer = document.getElementById('rating-stars-display');
    if (!starsContainer) return;
    
    // Clear existing stars
    starsContainer.innerHTML = '';
    
    // Add filled stars
    for (let i = 0; i < rating; i++) {
        const star = document.createElement('i');
        star.className = 'fas fa-star';
        starsContainer.appendChild(star);
    }
    
    // Add empty stars
    for (let i = rating; i < 5; i++) {
        const star = document.createElement('i');
        star.className = 'far fa-star';
        starsContainer.appendChild(star);
    }
}
