function listBannedPairs() {
    const table = document.getElementById('PairsTable');
    if (!table) {
        return 0;
    }
    const rows = table.getElementsByTagName('tr');
    const usernames = [];

    for (let row of rows) {
        const checkbox = row.querySelector('input[type="checkbox"]');
        const usernameCell = row.cells[1];

        if (checkbox && !checkbox.checked) {
            usernames.push(usernameCell.innerText);
        }
    }

    if (usernames.length == 0){
        return ' ';
    }

    return usernames.join(',');
}

function download_excel_and_show(){
    const excel_table_div = document.getElementById('ExcelTablesPanel');
    const download_fn = document.getElementById('DownloadExcelPath');
    
    const banned_pairs = listBannedPairs();

    if (typeof(banned_pairs) == 'number'){
        return;
    }

    axios.get(`/generate_excel_tables/${encodeURIComponent(banned_pairs)}`)
        .then(response => {
            excel_table_div.innerHTML = '';
            download_fn.textContent = response.data.xlsx_path;
        })
        .catch(error => {
            excel_table_div.value = error.error;
        });
}
/*
document.getElementById('DownloadExcelPath').addEventListener('change', (event) => {
    const file = event.textContent;
    console.log('HEH')
    const reader = new FileReader();
    reader.onload = function(e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, {type: 'array'});
        const sheetName = workbook.SheetNames[0];
        const sheetData = XLSX.utils.sheet_to_html(workbook.Sheets[sheetName]);
        document.getElementById('ExcelTablesPanel').innerHTML = sheetData;
    };
    reader.readAsArrayBuffer(file);
});*/