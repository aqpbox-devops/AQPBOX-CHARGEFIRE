function toggleFilter(button) {
    button.classList.toggle('active');
}

function toggleMannConnection(button) {
    const dbPath = document.getElementById('dbPath').value;

    axios.get(`/init_db/${encodeURIComponent(dbPath)}`)
        .then(response => {
            button.textContent = 'Conectado';
            button.style.backgroundColor = '#4CAF50';
            console.log(response.message)
        })
        .catch(error => {
            button.textContent = 'Error';
            button.style.backgroundColor = '#ff4444';
            console.log(error.message)
        });
}