function createEmployeeCard(emp, mode) {
    if (mode === 'default'){
        const card = document.createElement('div');
        const formattedCode = emp.employee_code.toString().padStart(11, '0');
        const formattedDNI = emp.employee_dni.toString().padStart(8, '0');
        card.className = 'employee-card';
        if (emp.selected) {
            card.style.border = '2px solid green'; // Borde verde
        }
        card.innerHTML = `
            <strong>Código OFISIS:</strong> ${formattedCode}<br>
            <strong>DNI:</strong> ${formattedDNI}<br>
            <strong>Nombre de Usuario:</strong> ${emp.username}<br>
            <strong>Nombres y Apellidos:</strong> ${emp.names}<br>
            <strong>Fecha de Inicio:</strong> ${emp.hire_date}
        `;
        return card;
    }
    else if (mode === 'indicator'){
        const card = document.createElement('tr');

        card.className = 'displayed-pairs-row';

        card.innerHTML = `
            <td><input type="checkbox" class="select-checkbox" ${emp.selected ? '' : 'checked'} /></td>
            <td>${emp.username}</td>
            <td>${emp.smeta}</td>
            <td>${emp.vmcbm}</td>
            <td>${emp.cmeta}</td>
            <td>${emp.vmcbc}</td>
            <td>${emp.pmeta}</td>
            <td>${emp.donton}</td>
        `;
        return card;
    }
    return null;
}

function displayResults(results, idContainer, mode) {
    const container = document.getElementById(idContainer);
    container.innerHTML = '';

    if (mode === 'indicator'){
        container.innerHTML = `
        <table class="displayed-pairs-panel" id="PairsTable">
            <thead>
                <tr>
                    <th>Es par</th>
                    <th>Analista</th>
                    <th>Crec. Saldo</th>
                    <th>Saldo Meta</th>
                    <th>Crec. Clientes</th>
                    <th>Clientes Meta</th>
                    <th>Desembolsos</th>
                    <th>Meta Desembolsos</th>
                </tr>
            </thead>
            <tbody id="PairsBody"></tbody>
        </table>
        `;
        const tbody = document.getElementById('PairsBody');
        results.forEach(emp => {
            const card = createEmployeeCard(emp, mode);
            tbody.appendChild(card);
        });
    }

    else{

        results.forEach(emp => {
            const card = createEmployeeCard(emp, mode);
            container.appendChild(card);
        });
    }
}

function clearElement(id_label){
    const element = document.getElementById(id_label);
    if (element) {
        element.innerHTML = '';
    }
}

document.getElementById('SearchEmployee').addEventListener('input', function(event) {
    const mode = document.getElementById('SearchMode').value;
    const query = event.target.value;
    const idContainer = 'EmployeeResults';

    clearElement('FilteredPairsResults');

    if (query == ''){
        clearElement(idContainer)
    }
    else{
        axios.get(`/search_employee/${encodeURIComponent(query)}/${encodeURIComponent(mode)}`)
            .then(response => {
                clearElement(idContainer);
                displayResults(response.data.employees, idContainer, 'default');
            })
            .catch(error => {
                clearElement(idContainer);
                document.getElementById(idContainer).value = error.error;
            });
    }
});