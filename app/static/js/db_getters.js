function clearElement(id){
    const e = document.getElementById(id);
    if (e){
        e.innerHTML = '';
    }
}

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
            <td><input type="checkbox" class="select-pair-checkbox" ${emp.selected ? '' : 'checked'} /></td>
            <td>${emp.username}</td>
            <td>${emp.vmcbm}</td>
            <td>${emp.smeta}</td>
            <td>${emp.vmcbc}</td>
            <td>${emp.cmeta}</td>
            <td>${emp.donton}</td>
            <td>${emp.pmeta}</td>
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
                    <th>
                        <label>
                            Es par
                            <input type="checkbox" id="ToggleAllCheckboxes" checked>
                        </label>
                    </th>
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

        document.getElementById('ToggleAllCheckboxes').addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('#PairsTable tbody .select-pair-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    else{

        results.forEach(emp => {
            const card = createEmployeeCard(emp, mode);
            container.appendChild(card);
        });
    }
}

function searchInPairsToHandle(filter){
    const lower_filter = filter.toLowerCase();
    const table = document.getElementById('PairsTable');
    const rows = table.getElementsByTagName('tr');

    if (table){

        for (let i = 1; i < rows.length; i++) {
            const cells = rows[i].getElementsByTagName('td');
            const analistaCell = cells[1];

            if (analistaCell) {
                const username = analistaCell.textContent || analistaCell.innerText;
                if (username.toLowerCase().indexOf(lower_filter) > -1) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        }
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

function buildAndSortRanking(sorted_emps, selectedIndicator, target_data) {
    searchInPairsToHandle("");

    const sortedTableContainer = document.getElementById('RankingTable');
    sortedTableContainer.innerHTML = '';

    const sortedTable = document.createElement('table');
    sortedTable.className = 'displayed-pairs-panel';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Analista</th>
            <th class="${selectedIndicator === 'vmcbm' ? 'highlight-column' : ''}">Crecimiento Saldo</th>
            <th>Saldo Meta</th>
            <th class="${selectedIndicator === 'vmcbc' ? 'highlight-column' : ''}">Crecimiento Clientes</th>
            <th>Clientes Meta</th>
            <th class="${selectedIndicator === 'donton' ? 'highlight-column' : ''}">Desembolsos</th>
            <th>Meta Desembolsos</th>
        </tr>`;
    sortedTable.appendChild(thead);

    const tbody = document.createElement('tbody');
    const table_ref = document.getElementById('PairsTable');
    const rows = table_ref.getElementsByTagName('tr');

    let totalValues = {
        crecimientoSaldo: 0,
        saldoMeta: 0,
        crecimientoClientes: 0,
        clientesMeta: 0,
        desembolsos: 0,
        metaDesembolsos: 0,
        count: 0
    };

    sorted_emps.forEach(emp => {
        const pairRow = Array.from(rows).find(row => {
            const usernameCell = row.getElementsByTagName('td')[1];
            return usernameCell && usernameCell.textContent.trim() === emp;
        });

        if (pairRow) {
            const checkbox = pairRow.querySelector('.select-pair-checkbox');

            if (checkbox && checkbox.checked) {
                const newRow = pairRow.cloneNode(true);
                newRow.className = 'displayed-pairs-row';
                const checkboxCell = newRow.querySelector('td');

                if (checkboxCell) {
                    checkboxCell.remove();
                }

                tbody.appendChild(newRow);

                totalValues.crecimientoSaldo += parseFloat(newRow.cells[1].textContent) || 0;
                totalValues.saldoMeta += parseFloat(newRow.cells[2].textContent) || 0;
                totalValues.crecimientoClientes += parseFloat(newRow.cells[3].textContent) || 0;
                totalValues.clientesMeta += parseFloat(newRow.cells[4].textContent) || 0;
                totalValues.desembolsos += parseFloat(newRow.cells[5].textContent) || 0;
                totalValues.metaDesembolsos += parseFloat(newRow.cells[6].textContent) || 0;
                totalValues.count++;
            }
        }
    });

    // Agregar fila del promedio del evaluado
    if (totalValues.count > 0) {
        const targetAverageRow = document.createElement('tr');
        const avg_target = target_data.full_avg_target.average[0];
        console.log(avg_target);
        targetAverageRow.innerHTML = `
            <td><strong>PROMEDIO</strong></td>
            <td>${avg_target.vmcbm.toFixed(2)}</td>
            <td>${avg_target.smeta.toFixed(2)}</td>
            <td>${avg_target.vmcbc.toFixed(2)}</td>
            <td>${avg_target.cmeta.toFixed(2)}</td>
            <td>${avg_target.donton.toFixed(2)}</td>
            <td>${avg_target.pmeta.toFixed(2)}</td>
        `;
        
        targetAverageRow.classList.add('sticky-target-average-row'); // Clase para estilo sticky
        tbody.insertBefore(targetAverageRow, tbody.firstChild); // Insertar justo debajo del encabezado
    }

    // Agregar fila de promedios
    if (totalValues.count > 0) {
        const averageRow = document.createElement('tr');
        averageRow.innerHTML = `
            <td><strong>PROMEDIO</strong></td>
            <td><strong>${(totalValues.crecimientoSaldo / totalValues.count).toFixed(2)}</strong></td>
            <td><strong>${(totalValues.saldoMeta / totalValues.count).toFixed(2)}</strong></td>
            <td><strong>${(totalValues.crecimientoClientes / totalValues.count).toFixed(2)}</strong></td>
            <td><strong>${(totalValues.clientesMeta / totalValues.count).toFixed(2)}</strong></td>
            <td><strong>${(totalValues.desembolsos / totalValues.count).toFixed(2)}</strong></td>
            <td><strong>${(totalValues.metaDesembolsos / totalValues.count).toFixed(2)}</strong></td>
        `;
        
        averageRow.classList.add('sticky-average-row'); // Asegúrate de que tenga el mismo estilo
        tbody.insertBefore(averageRow, tbody.firstChild); // Agregar la fila de promedios al tbody
    }

    sortedTable.appendChild(tbody);
    
    sortedTableContainer.appendChild(sortedTable);
}

function buildRankingTable(ranks, target_data){
    const ranking_buttons = document.getElementById('RankingButtons');
    ranking_buttons.innerHTML = '';

    const indicators_lookup = {};
    indicators_lookup['vmcbm'] = 'Crec. Saldo';
    indicators_lookup['vmcbc'] = 'Crec. Clientes';
    indicators_lookup['donton'] = 'Desembolsos';

    const indicators = Object.keys(ranks);
    indicators.forEach(indicator => {
        const button = document.createElement('button');
        button.textContent = indicators_lookup[indicator];
        button.onclick = () => buildAndSortRanking(ranks[indicator], indicator, target_data);
        ranking_buttons.appendChild(button);
    });
}

function setTargetAttrs(tables) {
    const target_attrs = document.getElementById('TargetAttrs');
    target_attrs.innerHTML = '';

    const attrs = tables.full_avg_target.attrs;
    console.log(attrs);

    const arrMonths = Object.values(attrs.months).map(date => new Date(date));

    const dateStart = new Date(Math.min(...arrMonths));
    const dateEnd = new Date(Math.max(...arrMonths));

    const stringfyDate = (date) => {
        const options = { year: 'numeric', month: 'long' };
        const formattedDate = date.toLocaleDateString('es-ES', options);
        
        return formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1);
    };

    const dateFormatedStart = stringfyDate(dateStart);
    const dateFormatedEnd = stringfyDate(dateEnd);

    target_attrs.innerHTML += `
        <strong>Región:</strong> ${attrs.region}<br>
        <strong>Zona:</strong> ${attrs.zone}<br>
        <strong>Agencia:</strong> ${attrs.agency}<br>
        <strong>Categoría:</strong> ${attrs.category}<br>
        <strong>Meses Considerados:</strong> Desde ${dateFormatedStart} a ${dateFormatedEnd}<br>
    `;
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function getEachMonthToBan(start_date, end_date) {
    const bannedMonthsElement = document.getElementById('BannedMonths');

    const existingCheckboxes = Array.from(bannedMonthsElement.querySelectorAll('.month-exception'));
    const existingStates = {};
    
    existingCheckboxes.forEach(checkbox => {
        existingStates[checkbox.id] = checkbox.checked;
    });

    bannedMonthsElement.innerHTML = '';

    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

    let currentDate = new Date(start_date);

    while (currentDate <= end_date) {
        const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        const formattedDate = formatDate(lastDayOfMonth);
        const checkboxId = `month-${currentDate.getTime()}`;

        let isChecked = existingStates[checkboxId] !== undefined ? existingStates[checkboxId] : true; // Valor por defecto es false si no existe

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = `month-exception`;
        checkbox.value = formattedDate;
        checkbox.id = checkboxId;
        checkbox.checked = isChecked;

        localStorage.setItem(checkbox.id, isChecked);

        checkbox.addEventListener('change', function() {
            localStorage.setItem(checkbox.id, checkbox.checked);
        });

        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.appendChild(document.createTextNode(`${months[currentDate.getMonth()]}, ${currentDate.getFullYear()}`));

        const div = document.createElement('div');
        div.appendChild(checkbox);
        div.appendChild(label);

        bannedMonthsElement.appendChild(div);

        currentDate.setMonth(currentDate.getMonth() + 1);
    }
}

function getDateRange() {
    const selectedMonth = parseInt(document.getElementById('SelectedMonth').value);
    const monthsBack = parseInt(document.getElementById('MonthsBack').value);

    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();

    const start_date = new Date(currentYear, selectedMonth - monthsBack, 1);
    const end_date = new Date(currentYear, selectedMonth, 1);
    end_date.setDate(end_date.getDate() - 1);

    return [start_date, end_date];
}

function genMonthsExceptions(){
    const [start_date_dt, end_date_dt] = getDateRange();

    getEachMonthToBan(start_date_dt, end_date_dt);
}

const selectedMonth = document.getElementById('SelectedMonth');
const monthsBack = document.getElementById('MonthsBack');
selectedMonth.addEventListener('change', genMonthsExceptions);
monthsBack.addEventListener('input', genMonthsExceptions);

function getSelectedMonths() {
    const checkboxes = document.querySelectorAll('.month-exception:not(:checked)');
    const selectedValues = Array.from(checkboxes).map(checkbox => checkbox.value);

    return selectedValues;
}

document.getElementById('FiltersPanel').addEventListener('click', function(event) {
    const [start_date_dt, end_date_dt] = getDateRange();

    const start_date = formatDate(start_date_dt);
    const end_date = formatDate(end_date_dt);

    if (event.target.tagName === 'BUTTON') {
        const region = document.getElementById('FlagRegion').classList.contains('active');
        const zone = document.getElementById('FlagZone').classList.contains('active');
        const agency = document.getElementById('FlagAgency').classList.contains('active');
        
        const monthly = document.getElementById("MonthlyCheck").checked;
        const banned_months = getSelectedMonths();

        const flags = {
            region,
            zone,
            agency,
            banned_months,
            start_date,
            end_date
        };

        const idContainer = 'FilteredPairsResults';

        axios.post('/search_pairs', flags)
            .then(response => {
                if (response.data.pairs.length > 0){
                    displayResults(response.data.pairs, idContainer, 'indicator');
                    setTargetAttrs(response.data.tables);
                    buildRankingTable(response.data.ranks, response.data.tables);
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

document.getElementById('PairFinderInTable').addEventListener('keyup', function() {
    searchInPairsToHandle(this.value);
});