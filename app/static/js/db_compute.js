function showTable(tableId) {
    // Ocultar todas las tablas
    const tables = document.querySelectorAll('.table-content');
    tables.forEach(table => {
        table.style.display = 'none';
    });

    // Mostrar la tabla seleccionada
    const selectedTable = document.getElementById(tableId);
    if (selectedTable) {
        selectedTable.style.display = 'block';
    }
}