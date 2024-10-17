function createEmployeeCard(emp) {
    const card = document.createElement('div');
    const formattedCode = emp.employee_code.toString().padStart(11, '0');
    const formattedDNI = emp.employee_dni.toString().padStart(8, '0');
    card.className = 'employee-card';
    card.innerHTML = `
        <strong>Código OFISIS:</strong> ${formattedCode}<br>
        <strong>DNI:</strong> ${formattedDNI}<br>
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

document.getElementById('SearchEmployee').addEventListener('input', function(event) {
    const mode = document.getElementById('SearchMode').value;
    const query = event.target.value;
    const idContainer = 'EmployeeResults'

    axios.get(`/search_employee/${encodeURIComponent(query)}/${encodeURIComponent(mode)}`)
        .then(response => {
            displayResults(response.data.employees, idContainer);
        })
        .catch(error => {
            document.getElementById(idContainer).value = error.error
        });
});

document.getElementById('FiltersPanel').addEventListener('click', function(event) {
    const start_date = document.getElementById('StartDate').value;
    const end_date = document.getElementById('EndDate').value;
    if (event.target.tagName === 'BUTTON') {
        const region = document.getElementById('FlagRegion').classList.contains('active')
        const zone = document.getElementById('FlagZone').classList.contains('active')
        const agency = document.getElementById('FlagAgency').classList.contains('active')
        const category = document.getElementById('FlagCategory').classList.contains('active')
        const atLeast15 = document.getElementById('FlagAtLeast15').classList.contains('active')
        const goals = document.getElementById('FlagGoals').classList.contains('active')
        
        const flags = {
            region,
            zone,
            agency,
            category,
            atLeast15,
            goals,
            start_date,
            end_date
        };

        const idContainer = 'FilteredPairsResults';

        axios.post('/search_pairs', flags)
            .then(response => {
                displayResults(response.data.employees, idContainer);
            })
            .catch(error => {
                document.getElementById(idContainer).value = error.error
            });
    }
});