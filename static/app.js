async function fetchJson(url, options = {}) {
    options.headers = {
        Accept: 'application/json',
        ...(options.headers || {}),
    };

    const response = await fetch(url, options);
    const contentType = response.headers.get('content-type') || '';
    const text = await response.text();

    let data;
    if (contentType.includes('application/json')) {
        try {
            data = JSON.parse(text);
        } catch (err) {
            throw new Error(`Invalid JSON response (${response.status})`);
        }
    }

    if (!response.ok) {
        const message = data?.error || text || `Request failed with status ${response.status}`;
        throw new Error(message);
    }

    if (data === undefined) {
        throw new Error('Expected JSON response but received non-JSON content');
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