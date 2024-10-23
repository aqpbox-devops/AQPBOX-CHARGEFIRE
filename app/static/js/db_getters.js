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

        card.className = 'displayed-pairs-row'

        card.innerHTML = `
            <td><input type="checkbox" class="select-checkbox" checked /></td>
            <td>${emp.username}</td>
            <td>${emp.smeta}</td>
            <td>${emp.growth_s}</td>
            <td>${emp.cmeta}</td>
            <td>${emp.growth_c}</td>
            <td>${emp.pmeta}</td>
            <td>${emp.productivity}</td>
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
        <table class="displayed-pairs-pannel" id="PairsTable">
            <thead>
                <tr>
                    <th>Es par</th>
                    <th>Analista</th>
                    <th>Crec. Saldo</th>
                    <th>→Meta</th>
                    <th>Crec. Clientes</th>
                    <th>→Meta</th>
                    <th>Desembolso</th>
                    <th>→Meta</th>
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
    const idContainer = 'EmployeeResults'

    clearElement('FilteredPairsResults')

    if (query == ''){
        clearElement(idContainer)
    }
    else{
        axios.get(`/search_employee/${encodeURIComponent(query)}/${encodeURIComponent(mode)}`)
            .then(response => {
                clearElement(idContainer)
                displayResults(response.data.employees, idContainer, 'default');
            })
            .catch(error => {
                clearElement(idContainer)
                document.getElementById(idContainer).value = error.error
            });
    }
});

document.getElementById('FiltersPanel').addEventListener('click', function(event) {
    const start_date = document.getElementById('StartDate').value;
    const end_date = document.getElementById('EndDate').value;
    if (event.target.tagName === 'BUTTON') {
        const region = document.getElementById('FlagRegion').classList.contains('active')
        const zone = document.getElementById('FlagZone').classList.contains('active')
        const agency = document.getElementById('FlagAgency').classList.contains('active')
        
        const flags = {
            region,
            zone,
            agency,
            start_date,
            end_date
        };

        const idContainer = 'FilteredPairsResults';

        axios.post('/search_pairs', flags)
            .then(response => {
                if (response.data.pairs.length > 0){
                    displayResults(response.data.pairs, idContainer, 'indicator');
                    const pairs_table = document.getElementById('PairsTable')
                    const worstUsernames = response.data.worst;

                    const rows = pairs_table.getElementsByTagName('tr');
                    for (let i = 0; i < rows.length; i++) {
                        const usernameCell = rows[i].getElementsByTagName('td')[1];
                        
                        if (usernameCell) {
                            const username = usernameCell.textContent.trim();

                            if (worstUsernames.includes(username)) {
                                const checkbox = rows[i].querySelector('.select-checkbox');
                                if (checkbox) {
                                    checkbox.checked = false;
                                }
                            }
                        }
                    }

                    const ranking_buttons = document.getElementById('RankingButtons');
                    ranking_buttons.innerHTML = ''; // Limpiar el panel antes de agregar

                    // Crear botones para cada indicador
                    const indicators = Object.keys(response.data.ranks);
                    indicators.forEach(indicator => {
                        const button = document.createElement('button');
                        button.textContent = `Ranking por ${indicator}`;
                        button.onclick = () => sortTable(indicator); // Llama a la función para ordenar
                        ranking_buttons.appendChild(button);
                    });

                    // Crear un contenedor para la tabla ordenada
                    const sortedTableContainer = document.getElementById('RankingTable');

                    // Función para ordenar y mostrar la tabla
                    function sortTable(indicator) {
                        // Limpiar el contenedor de la tabla ordenada antes de mostrar una nueva
                        sortedTableContainer.innerHTML = '';

                        // Obtener los rankings del indicador seleccionado
                        const ranks = response.data.ranks[indicator];

                        // Crear una nueva tabla sin checkboxes
                        const sortedTable = document.createElement('table');
                        sortedTable.className = 'displayed-pairs-pannel'; // Agregar clase para estilos

                        // Crear encabezados
                        const thead = document.createElement('thead');
                        thead.innerHTML = `
                            <tr>
                                <th>Analista</th>
                                <th>Crecimiento Saldo</th>
                                <th>Saldo Meta</th>
                                <th>Crecimiento Clientes</th>
                                <th>Clientes Meta</th>
                                <th>Desembolso</th>
                                <th>Meta Desembolso</th>
                            </tr>`;
                        sortedTable.appendChild(thead);

                        // Crear tbody
                        const tbody = document.createElement('tbody');

                        // Reordenar los pares según los rankings
                        ranks.forEach(rank => {
                            const pairRow = Array.from(rows).find(row => {
                                const usernameCell = row.getElementsByTagName('td')[1];
                                return usernameCell && usernameCell.textContent.trim() === rank;
                            });

                            if (pairRow) {
                                // Clonar la fila sin el checkbox
                                const newRow = pairRow.cloneNode(true);
                                newRow.querySelector('.select-checkbox').remove(); // Eliminar el checkbox
                                tbody.appendChild(newRow);
                            }
                        });

                        sortedTable.appendChild(tbody);
                        
                        // Agregar la tabla ordenada al contenedor debajo de los botones
                        sortedTableContainer.appendChild(sortedTable);
                    }
                }
                else{
                    document.getElementById(idContainer).textContent = 'No se encontraron pares'
                }
            })
            .catch(error => {
                document.getElementById(idContainer).value = error.error
            });
    }
});