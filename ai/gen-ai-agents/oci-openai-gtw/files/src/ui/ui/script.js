// Load the REST URL 
function loadRest() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("json").innerHTML =
                this.responseText;
            let jsonValue = JSON.parse( this.responseText );    
            json2table(jsonValue);
        }
    };
    xhttp.open("GET", "app/dept", true);
    xhttp.send();

    var xhttp2 = new XMLHttpRequest();
    xhttp2.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("info").innerHTML =
                this.responseText;
        }
    };
    xhttp2.open("GET", "app/info", true);
    xhttp2.send();
}

// Convert the json in a HTML Table 
function json2table(jsonValue) {
    // Extract value from table header. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    let col = [];
    for (let i = 0; i < jsonValue.length; i++) {
        for (let key in jsonValue[i]) {
            if (col.indexOf(key) === -1) {
                col.push(key);
            }
        }
    }

    // Create table.
    const table = document.createElement("table");

    // Create table header row using the extracted headers above.
    let tr = table.insertRow(-1);                   // table row.

    for (let i = 0; i < col.length; i++) {
        let th = document.createElement("th");      // table header.
        th.innerHTML = col[i].toUpperCase();;
        tr.appendChild(th);
    }

    // add json data to the table as rows.
    for (let i = 0; i < jsonValue.length; i++) {
        tr = table.insertRow(-1);
        for (let j = 0; j < col.length; j++) {
            let tabCell = tr.insertCell(-1);
            tabCell.innerHTML = jsonValue[i][col[j]];
        }
    }

    // Now, add the newly created table with json data, to a container.
    const divData = document.getElementById('table');
    divData.innerHTML = "";
    divData.appendChild(table);
}