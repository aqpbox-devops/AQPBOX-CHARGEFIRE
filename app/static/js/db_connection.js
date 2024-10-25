function initializeDatabase() {
    axios.get(`/init_db`)
        .then(response => {
            console.log(response.data.message);
        })
        .catch(error => {
            console.error(error.message);
        });
}

window.onload = function() {
    initializeDatabase();
};