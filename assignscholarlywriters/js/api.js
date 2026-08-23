const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? (window.location.protocol + '//' + window.location.hostname + ':8000/api')
  : (window.location.origin + '/api');

const ScholarlyAPI = {
    // Fetch all academic levels
    async getAcademicLevels() {
        const resp = await fetch(`${API_BASE}/services/levels/`);
        return resp.json();
    },

    // Fetch all service types
    async getServiceTypes() {
        const resp = await fetch(`${API_BASE}/services/types/`);
        return resp.json();
    },

    // Fetch all deadline options
    async getDeadlines() {
        const resp = await fetch(`${API_BASE}/pricing/deadlines/`);
        return resp.json();
    },

    // Fetch all currencies
    async getCurrencies() {
        const resp = await fetch(`${API_BASE}/currencies/`);
        return resp.json();
    },

    // Calculate estimated price
    async calculatePrice(data) {
        const resp = await fetch(`${API_BASE}/quotations/calculate/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return resp.json();
    },

    // Submit quotation request (with file support)
    async submitQuotation(formData) {
        const resp = await fetch(`${API_BASE}/quotations/create/`, {
            method: 'POST',
            body: formData, // FormData object for file uploads
        });
        return resp.json();
    },

    // Track quotation by request ID or email
    async trackQuotation(requestId) {
        const resp = await fetch(`${API_BASE}/quotations/${requestId}/`);
        return resp.json();
    },

    // Get quotation list by email
    async getQuotationsByEmail(email) {
        const resp = await fetch(`${API_BASE}/quotations/list/?email=${encodeURIComponent(email)}`);
        return resp.json();
    },

    // Create PayPal payment
    async createPayment(orderId, currencyCode) {
        const resp = await fetch(`${API_BASE}/payments/create/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, currency_code: currencyCode }),
        });
        return resp.json();
    },

    // Execute PayPal payment
    async executePayment(paymentId, payerId, orderId) {
        const resp = await fetch(`${API_BASE}/payments/execute/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paypal_payment_id: paymentId,
                payer_id: payerId,
                order_id: orderId,
            }),
        });
        return resp.json();
    },
};

window.ScholarlyAPI = ScholarlyAPI;
