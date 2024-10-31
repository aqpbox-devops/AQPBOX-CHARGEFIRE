function initializeDatabase() {
    document.getElementById('loadingScreen').style.display = 'flex';

    let progress = 0;
    const progressBar = document.getElementById('progress');
    
    const interval = setInterval(() => {
        progress += 10;
        if (progress <= 100) {
            progressBar.style.width = progress + '%';
        }
        if (progress >= 100) {
            clearInterval(interval);
        }
    }, 400);

    axios.get(`/init_db`)
        .then(response => {
            console.log(response.data.message);
            setTimeout(() => {
                document.getElementById('loadingScreen').style.display = 'none';
            }, 500);
        })
        .catch(error => {
            console.error(error.message);
            document.getElementById('loadingMessage').innerText = "Hubo un error al cargar la base de datos. Por favor, intenta nuevamente.";
            setTimeout(() => {
                document.getElementById('loadingScreen').style.display = 'none';
            }, 2000);
        });
}

window.onload = function() {
    initializeDatabase();
};