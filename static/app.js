function escapeHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function fetchJson(url, options) {
    const response = await fetch(url, options);
    const text = await response.text();
    let data = {};

    try {
        if (text) {
            data = JSON.parse(text);
        }
    } catch (error) {
        // Provide a more specific message based on HTTP status when server returns non-JSON (HTML/error page)
        if (!response.ok) {
            if (response.status >= 500) {
                throw new Error('Server error. Please try again later.');
            } else if (response.status === 401) {
                throw new Error('Invalid email or password.');
            } else if (response.status === 400) {
                throw new Error('Invalid input. Please check your details and try again.');
            }
        }

        throw new Error('Unable to parse server response. Please try again.');
    }

    if (!response.ok) {
        throw new Error(data.error || data.message || 'Login failed. Please check your credentials and try again.');
    }

    return data;
}

// this handles saving login info
window.KanoonAuth = {
    saveAuth: function(data) {
        localStorage.setItem('user', JSON.stringify(data));
    },
    getAuth: function() {
        return JSON.parse(localStorage.getItem('user'));
    },
    logout: function() {
        localStorage.removeItem('user');
    }
};