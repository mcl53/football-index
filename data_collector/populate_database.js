const secrets = require("./secrets");
const api = require("./fi_api_calls");
const handlers = require("./api_response_handlers");
const fs = require("fs");
const csv = require("csv-parser");

const firstMediaDate = new Date("2019-10-22");

function dateToString(date) {
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

function getMediaScores(dateString) {
    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    api.sendRequest(url, handlers.saveMediaScores, dateString);
}

function downloadAllMediaScores() {
    let curerntDate = firstMediaDate;
    const todaysDate = new Date();

    while (currentDate <= todaysDate) {
        let currentDateStr = dateToString(currentDate);
        getMediaScores(currentDateStr);
        currentDate.setTime(currentDate.getTime() + 86400000);
    }
}

function downloadAllPlayerPrices() {
    let currentDate = firstMediaDate;
    const todaysDate = new Date();

    while (currentDate <= todaysDate) {
        let currentDateStr = dateToString(currentDate);
        let currentMediaFile = `../media_scores/${currentDateStr}.csv`;

        fs.createReadStream(currentMediaFile)
        .pipe(csv())
        .on("data", row => {
            if(!fs.existsSync(`../player_prices/${row.urlname}.csv`)) {
                updatePlayerPrices(row.urlname);
            }
        });
    }
}