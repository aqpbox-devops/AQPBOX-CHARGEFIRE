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
                    <th>Desembolsos</th>
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

function buildAndSortRanking(sorted_emps, selectedIndicator) {
    const sortedTableContainer = document.getElementById('RankingTable');
    sortedTableContainer.innerHTML = '';

    const sortedTable = document.createElement('table');
    sortedTable.className = 'displayed-pairs-pannel';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Analista</th>
            <th class="${selectedIndicator === 'growth_s' ? 'highlight-column' : ''}">Crecimiento Saldo</th>
            <th>Saldo Meta</th>
            <th class="${selectedIndicator === 'growth_c' ? 'highlight-column' : ''}">Crecimiento Clientes</th>
            <th>Clientes Meta</th>
            <th class="${selectedIndicator === 'productivity' ? 'highlight-column' : ''}">Desembolsos</th>
            <th>Meta Desembolsos</th>
        </tr>`;
    sortedTable.appendChild(thead);

    const tbody = document.createElement('tbody');
    const table_ref = document.getElementById('PairsTable');
    const rows = table_ref.getElementsByTagName('tr');

    sorted_emps.forEach(emp => {
        const pairRow = Array.from(rows).find(row => {
            const usernameCell = row.getElementsByTagName('td')[1];
            return usernameCell && usernameCell.textContent.trim() === emp;
        });

        if (pairRow) {
            const checkbox = pairRow.querySelector('.select-checkbox');

            if (checkbox && checkbox.checked) {
                const newRow = pairRow.cloneNode(true);
                newRow.className = 'displayed-pairs-row';
                const checkboxCell = newRow.querySelector('td');
                
                if (checkboxCell) {
                    checkboxCell.remove();
                }

                tbody.appendChild(newRow);
            }
        }
    });

    sortedTable.appendChild(tbody);
    
    sortedTableContainer.appendChild(sortedTable);
}

function buildRankingTable(ranks){
    const ranking_buttons = document.getElementById('RankingButtons');
    ranking_buttons.innerHTML = '';

    const indicators_lookup = {};
    indicators_lookup['growth_s'] = 'Crec. Saldo';
    indicators_lookup['growth_c'] = 'Crec. Clientes';
    indicators_lookup['productivity'] = 'Desembolsos';

    const indicators = Object.keys(ranks);
    indicators.forEach(indicator => {
        const button = document.createElement('button');
        button.textContent = indicators_lookup[indicator];
        button.onclick = () => buildAndSortRanking(ranks[indicator], indicator);
        ranking_buttons.appendChild(button);
    });
}

function getDateRange() {
    const selectedMonth = parseInt(document.getElementById('SelectedMonth').value);
    const monthsBack = parseInt(document.getElementById('MonthsBack').value);

    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();

    const start_month = selectedMonth - 1;
    const start_date = new Date(currentYear, start_month - monthsBack, 1);
    const end_date = new Date(currentYear, start_month, 0);

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    return [formatDate(start_date), formatDate(end_date)];
}

document.getElementById('FiltersPanel').addEventListener('click', function(event) {
    const [start_date, end_date] = getDateRange();

    if (event.target.tagName === 'BUTTON') {
        const region = document.getElementById('FlagRegion').classList.contains('active');
        const zone = document.getElementById('FlagZone').classList.contains('active');
        const agency = document.getElementById('FlagAgency').classList.contains('active');
        
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
                    buildRankingTable(response.data.ranks);
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