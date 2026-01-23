/**
 * SIMPLIFIED VERSION - Newsletter Subscription Handler
 * This will show you exactly what's happening
 */

class NewsletterSubscription {
    constructor() {
        console.log('NewsletterSubscription initialized');
        
        // DOM Elements
        this.form = $('#subscriptionForm');
        this.emailInput = $('#userEmail');
        this.nameInput = $('#userName');
        this.submitBtn = $('#submitBtn') || $('#submit');
        this.errorDiv = $('#errorMessage');
        this.successDiv = $('#successMessage');
        
        // Debug: Check if elements exist
        console.log('Form found:', this.form.length > 0);
        console.log('Email input found:', this.emailInput.length > 0);
        console.log('Name input found:', this.nameInput.length > 0);
        console.log('Submit button found:', this.submitBtn.length > 0);
        console.log('Error div found:', this.errorDiv.length > 0);
        console.log('Success div found:', this.successDiv.length > 0);
        
        // Initialize
        this.bindEvents();
        this.setupCSRF();
    }
    
    setupCSRF() {
        // Simple CSRF setup
        const csrftoken = $('[name=csrfmiddlewaretoken]').val();
        console.log('CSRF token:', csrftoken ? 'Found' : 'Not found');
        
        if (csrftoken) {
            $.ajaxSetup({
                headers: {
                    "X-CSRFToken": csrftoken
                }
            });
        }
    }
    
    bindEvents() {
        console.log('Binding events...');
        
        // Handle form submission
        this.form.on('submit', (e) => {
            console.log('Form submitted!');
            e.preventDefault(); // Prevent default form submission
            this.handleSubmit(e);
        });
        
        // Also bind to button click (in case form submission isn't working)
        this.submitBtn.on('click', (e) => {
            console.log('Button clicked!');
            e.preventDefault();
            this.handleSubmit(e);
        });
    }
    
    showMessage(type, message) {
        console.log(`Showing ${type} message:`, message);
        
        // Clear any existing messages
        this.hideMessages();
        
        if (type === 'error') {
            this.errorDiv.html(`
                <div style="color: #dc3545; padding: 10px; background: #f8d7da; border-radius: 5px; margin: 10px 0;">
                    <strong>Error:</strong> ${message}
                </div>
            `).show();
        } else if (type === 'success') {
            this.successDiv.html(`
                <div style="color: #28a745; padding: 10px; background: #d4edda; border-radius: 5px; margin: 10px 0;">
                    <strong>Success:</strong> ${message}
                </div>
            `).show();
        }
    }
    
    hideMessages() {
        this.errorDiv.hide().empty();
        this.successDiv.hide().empty();
    }
    
    showLoading() {
        console.log('Showing loading state');
        const originalText = this.submitBtn.html();
        this.submitBtn.data('original-text', originalText);
        this.submitBtn.prop('disabled', true).html(`
            <span style="display: inline-block; width: 16px; height: 16px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 8px;"></span>
            Processing...
        `);
    }
    
    hideLoading() {
        console.log('Hiding loading state');
        const originalText = this.submitBtn.data('original-text') || 'Subscribe Now';
        this.submitBtn.prop('disabled', false).html(originalText);
    }
    
    validateForm() {
        console.log('Validating form...');
        
        const email = this.emailInput.val().trim();
        const name = this.nameInput.val().trim();
        
        console.log('Email:', email);
        console.log('Name:', name);
        
        // Simple validation
        if (!email) {
            this.showMessage('error', 'Email is required');
            return false;
        }
        
        if (!name) {
            this.showMessage('error', 'Name is required');
            return false;
        }
        
        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showMessage('error', 'Please enter a valid email address');
            return false;
        }
        
        this.hideMessages();
        return true;
    }
    
    async handleSubmit(event) {
        console.log('handleSubmit called');
        
        // Prevent multiple submissions
        if (this.submitBtn.prop('disabled')) {
            console.log('Already submitting, skipping...');
            return;
        }
        
        // Validate form
        if (!this.validateForm()) {
            console.log('Form validation failed');
            return;
        }
        
        const email = this.emailInput.val().trim();
        const name = this.nameInput.val().trim();
        
        console.log('Submitting:', { email, name });
        
        // Show loading
        this.showLoading();
        
        try {
            // Submit to server
            const response = await this.submitToServer(email, name);
            console.log('Server response:', response);
            
            if (response.success) {
                this.showMessage('success', response.msg || 'Subscription successful!');
                // Clear form
                this.form[0].reset();
            } else {
                this.showMessage('error', response.error || response.msg || 'Subscription failed');
            }
            
        } catch (error) {
            console.error('Submission error:', error);
            this.showMessage('error', 'An error occurred. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    submitToServer(email, name) {
        console.log('Sending request to server...');
        
        return new Promise((resolve, reject) => {
            $.ajax({
                url: '/subscribe/',  // Make sure this matches your Django URL
                type: 'POST',
                data: {
                    email: email,
                    name: name,
                    csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                },
                dataType: 'json',
                success: (response) => {
                    console.log('AJAX success:', response);
                    resolve(response);
                },
                error: (xhr, status, error) => {
                    console.error('AJAX error:', { xhr, status, error });
                    
                    let errorMsg = 'Network error. Please try again.';
                    
                    if (xhr.responseJSON) {
                        errorMsg = xhr.responseJSON.error || xhr.responseJSON.msg || errorMsg;
                    } else if (xhr.status === 0) {
                        errorMsg = 'No internet connection. Please check your network.';
                    } else if (xhr.status === 500) {
                        errorMsg = 'Server error. Please try again later.';
                    }
                    
                    reject(new Error(errorMsg));
                }
            });
        });
    }
}

// Initialize when document is ready
$(document).ready(function() {
    console.log('Document ready, initializing newsletter...');
    
    // Check if jQuery is loaded
    if (typeof jQuery === 'undefined') {
        console.error('jQuery is not loaded!');
        return;
    }
    
    // Create newsletter instance
    const newsletter = new NewsletterSubscription();
    
    // Make it globally available for debugging
    window.newsletter = newsletter;
    
    console.log('Newsletter initialized successfully');
});