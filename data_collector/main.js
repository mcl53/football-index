const api = require("./fi_api_calls");
const handlers = require("./api_response_handlers");
const secrets = require("./secrets");
const fs = require("fs");
const csv = require("csv-parser");

function todaysDateString() {
    const todaysDate = new Date();
    const day = String(todaysDate.getDate()).padStart(2, "0");
    const month = String(todaysDate.getMonth() + 1).padStart(2, "0");
    const year = String(todaysDate.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

function getNewMediaScores() {
    const dateString = todaysDateString();
    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    api.sendRequest(url, handlers.saveMediaScores, dateString);
}

function updatePlayerPrices(playerName) {
    url = `${secrets.price_history_endpoint}${playerName}`;

    api.sendRequest(url, handlers.savePlayerPrices, playerName);
}

function updateTodaysPlayers() {
    const dateString = todaysDateString();
    fileName = `../media_scores/${dateString}.csv`;

    fs.createReadStream(fileName)
        .pipe(csv())
        .on("data", row => {
            updatePlayerPrices(row.urlname);
        });
}

getNewMediaScores();
updateTodaysPlayers();