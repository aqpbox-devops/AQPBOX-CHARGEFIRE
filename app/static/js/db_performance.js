function calculateYearsAndMonths(longevity) {
    const years = parseInt(longevity / 12);
    const months = parseInt(longevity % 12);

    let output = "";
    if (years > 0) {
        output += `${years} año${years > 1 ? 's' : ''}`;
    }
    if (months > 0) {
        if (output) output += ' y ';
        output += `${months} mes${months > 1 ? 'es' : ''}`;
    }

    if (!output) {
        output = "0 meses";
    }

    return output;
}

function setText(idElement, text){
    const element = document.getElementById(idElement);
    if (element){
        element.textContent = text;
    }
}

function insert_cells_by_group(group, column_start) {
    const body = document.getElementById('APTBody');

    for (const [rowIndex, values] of Object.entries(group)) {
        const row = body.rows[rowIndex - 1];
        let cellIndex = column_start;

        for (const key of Object.keys(values)) {
            if (cellIndex < row.cells.length) {
                const cell = row.cells[cellIndex];

                cell.textContent = isNaN(values[key]) ? 'N/A' : values[key];

                cellIndex++;
            }
        }
    }

    if (group['Avance hasta hoy']) {
        const avanceRow = body.rows[12];
        let avanceCellIndex = column_start;

        for (const key of Object.keys(group['Avance hasta hoy'])) {
            if (avanceCellIndex < avanceRow.cells.length) {
                const cell = avanceRow.cells[avanceCellIndex];

                cell.textContent = isNaN(group['Avance hasta hoy'][key]) ? 'N/A' : group['Avance hasta hoy'][key];

                avanceCellIndex++;
            }
        }
    }
}

function call_employee_stats(){
    axios.get(`/get_table`)
        .then(response => {
            const data = response.data.target;
            console.log(data);
            setText('ph-Analist', data.names);
            setText('ph-Agency', data.agency);
            setText('ph-Category', data.category);
            setText('ph-Longevity', calculateYearsAndMonths(data.longevity));

            insert_cells_by_group(data.data.A, 1);
            insert_cells_by_group(data.data.B, 6);
            insert_cells_by_group(data.data.C, 11);
            insert_cells_by_group(data.data.D, 13);
            insert_cells_by_group(data.data.E, 15);

        })
        .catch(error => {
            console.error(error.error);
        });
}

document.getElementById('SearchEmployee').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        call_employee_stats();
    }
});