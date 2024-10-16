function createEmployeeCard(emp) {
    const card = document.createElement('div');
    card.className = 'employee-card';
    card.innerHTML = `
        <strong>Código OFISIS:</strong> ${emp.employee_code}<br>
        <strong>Nombre de Usuario:</strong> ${emp.username}<br>
        <strong>Nombres y Apellidos:</strong> ${emp.names}<br>
        <strong>Fecha de Inicio:</strong> ${emp.hire_date}
    `;
    return card;
}

function displayResults(results, idContainer) {
    const container = document.getElementById(idContainer);
    container.innerHTML = '';
    results.forEach(emp => {
        const card = createEmployeeCard(emp);
        container.appendChild(card);
    });
}

document.getElementById('SearchEmployee').addEventListener('input', function(e) {
    const mode = document.getElementById('SearchMode').value;
    const query = e.target.value;
    const idContainer = 'EmployeeResults'

    axios.get(`/search_employee/${encodeURIComponent(query)}/${encodeURIComponent(mode)}`)
        .then(response => {
            displayResults(response.data.employees, idContainer);
        })
        .catch(error => {
            document.getElementById(idContainer).value = error.error
        });
});