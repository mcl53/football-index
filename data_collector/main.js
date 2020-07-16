const api = require("./fi_api_calls");
const handlers = require("./api_response_handlers");
const secrets = require("./secrets");
const fs = require("fs");
const csv = require("csv-parser");

let currentApiRequests = 0;
const maxApiRequests = 10;

function sleep(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

function todaysDateString() {
    const todaysDate = new Date();
    const day = String(todaysDate.getDate() - 1).padStart(2, "0");
    const month = String(todaysDate.getMonth() + 1).padStart(2, "0");
    const year = String(todaysDate.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

async function getNewMediaScores(dateString, callback) {
    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    await api.sendRequest(url, handlers.saveMediaScores, dateString);

    // Download new player data for the previous 2 days as this is used in model validation
    let yesterday = String(parseInt(dateString) - 1);
    let dayBefore = String(parseInt(dateString) - 2);
    callback(dateString);
    callback(yesterday);
    callback(dayBefore);
    
}

function updatePlayerPrices(playerName) {
    url = `${secrets.price_history_endpoint}${playerName}`;

    api.sendRequest(url, handlers.savePlayerPrices, playerName);
}

function updateTodaysPlayers(dateString) {
    fileName = `${secrets.basePath}/media_scores/${dateString}.csv`;

    fs.createReadStream(fileName)
        .pipe(csv())
        .on("data", async row => {
            currentApiRequests += 1;
            if (currentApiRequests > maxApiRequests) {
                let sleepTimes = Math.floor(currentApiRequests / maxApiRequests);
                await sleep(20000 * sleepTimes);
            }
            updatePlayerPrices(row.urlname);
        });
}

function execute() {
    const dateStr = todaysDateString();
    console.log(`Beginning script for ${dateStr}`);
    getNewMediaScores(dateStr, updateTodaysPlayers);
    console.log(`Ending script for ${dateStr}`);
}

execute();
