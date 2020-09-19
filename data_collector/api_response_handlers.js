const fs = require("fs");
const secrets = require("./secrets");

function jsonToCsv(json, headers) {
    /* This function expects to be passed a number of additional arguments greater than 1, 
    where each argument is the name of a column header for the csv file */

    // All json from this API contains data within an object assigned to the key 'items'
    let listOfObjects = json.items;

    if (!listOfObjects) {
        listOfObjects = json.days;
    }
    
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

    return toCsv;
}

async function saveMediaScores(json, dateStr) {
    const fileContents = jsonToCsv(json, ["name", "urlname", "score", "scoreSell"]);
    const fileName = `${secrets.basePath}/media_scores/${dateStr}.csv`;

    try {
        console.log(`Writing to file ${fileName}`);
        return await fs.promises.writeFile(fileName, fileContents);
    } catch(err) {
        console.log(err);
    }
}

function savePlayerPrices(json, playerName) {
    const fileContents = jsonToCsv(json, ["timestamp", "close"]);
    const fileName = `${secrets.basePath}/player_prices/${playerName}.csv`;

    fs.writeFile(fileName, fileContents, err => {
        if (err) {
            console.log(err);
        } else {
            console.log(`Written to file ${fileName}`);
        }
    });
}

module.exports = {
    saveMediaScores: saveMediaScores,
    savePlayerPrices: savePlayerPrices
};