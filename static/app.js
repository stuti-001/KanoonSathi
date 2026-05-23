async function fetchJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
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