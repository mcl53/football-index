const fs = require("fs");

function jsonToCsv(json, headers) {
    /* This function expects to be passed a number of additional arguments greater than 1, 
    where each argument is the name of a column header for the csv file */

    // All json from this API contains data within an object assigned to the key 'items'
    const listOfObjects = json.items;
    
    let toCsv = headers.join(",");

    /* Parse the data provided into rows. The column headers must be the names of keys in each object of the listOfObjects.
    Here we iterate through each obj in the listOfObjects and create a new row in the csv with each value chosen separated by a comma*/
    listOfObjects.forEach(obj => {
        toCsv += "\r\n";
        let newLine = headers.map(header => {
            return `${obj[header]}`;
        });
        toCsv += newLine.join(",")
        toCsv.slice(0, -1);
    });
    // console.log(toCsv);
    return toCsv;
    // fs.writeFile("./test.csv", toCsv, (err, written) => {
    //     if (err) {
    //         console.log(err);
    //         return;
    //     } else {
    //         console.log(`Bytes written: ${written}`);
    //     }
    // });
}

function saveMediaScores(json, dateStr) {
    const fileContents = jsonToCsv(json, ["name", "score"]);
    const fileName = `../media_scores/${dateStr}.csv`;

    fs.writeFile(fileName, fileContents, (err, written) => {
        if (err) {
            console.log(err);
            return;
        } else {
            console.log(`${written} bytes to file ${fileName}`)
        }
    });
}