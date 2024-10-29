function initializeDatabase() {
    // Mostrar la pantalla de carga
    document.getElementById('loadingScreen').style.display = 'flex';

    // Simulación de progreso (opcional)
    let progress = 0;
    const progressBar = document.getElementById('progress');
    
    const interval = setInterval(() => {
        progress += 10; // Incremento del progreso
        if (progress <= 100) {
            progressBar.style.width = progress + '%'; // Actualiza el ancho de la barra
        }
        if (progress >= 100) {
            clearInterval(interval); // Detener el intervalo cuando llegue al 100%
        }
    }, 400); // Cambia esto para ajustar la velocidad del progreso

    axios.get(`/init_db`)
        .then(response => {
            console.log(response.data.message);
            // Aquí puedes ocultar el loadingScreen después de un breve retraso
            setTimeout(() => {
                document.getElementById('loadingScreen').style.display = 'none';
            }, 500); // Ocultar después de medio segundo
        })
        .catch(error => {
            console.error(error.message);
            // Mostrar mensaje de error
            document.getElementById('loadingMessage').innerText = "Hubo un error al cargar la base de datos. Por favor, intenta nuevamente.";
            setTimeout(() => {
                document.getElementById('loadingScreen').style.display = 'none';
            }, 2000); // Ocultar después de 2 segundos
        });
}

window.onload = function() {
    initializeDatabase();
};