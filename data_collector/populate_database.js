const secrets = require("./secrets");
const api = require("./fi_api_calls");
const handlers = require("./api_response_handlers");
const fs = require("fs");
const csv = require("csv-parser");

const firstMediaDate = new Date("2019-10-22");
const maxApiRequests = 50;
let currentApiRequests = 0;

function dateToString(date) {
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

function sleep(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

function getMediaScores(dateString) {
    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    api.sendRequest(url, handlers.saveMediaScores, dateString);
}

async function downloadAllMediaScores() {
    let currentDate = firstMediaDate;
    const todaysDate = new Date().setHours(0, 0, 0, 0);
    while (currentDate < todaysDate) {
        let currentDateStr = dateToString(currentDate);
        getMediaScores(currentDateStr);
        currentApiRequests += 1;
        if (currentApiRequests >= maxApiRequests) {
            await sleep(60000);
            currentApiRequests = 0;
        }
        currentDate.setTime(currentDate.getTime() + 86400000);
    }
}

function updatePlayerPrices(playerName) {
    url = `${secrets.price_history_endpoint}${playerName}`;

    api.sendRequest(url, handlers.savePlayerPrices, playerName);
}

async function downloadAllPlayerPrices() {
    let currentDate = firstMediaDate;
    const todaysDate = new Date().setHours(0, 0, 0, 0);

    while (currentDate < todaysDate) {
        let currentDateStr = dateToString(currentDate);
        let currentMediaFile = `../media_scores/${currentDateStr}.csv`;
        currentDate.setTime(currentDate.getTime() + 86400000);
        console.log(currentMediaFile);
        let readStream = fs.createReadStream(currentMediaFile);
        let data = readStream.pipe(csv());
        
        data.on("data", async row => {
            if (currentApiRequests >= maxApiRequests) {
                let sleepTimes = Math.floor(currentApiRequests / maxApiRequests);
                await sleep(60000 * sleepTimes);
            }
            if (!fs.existsSync(`../player_prices/${row.urlname}.csv`)) {
                updatePlayerPrices(row.urlname);
                currentApiRequests += 1;
            }
        });
    }
}

async function execute() {
    await downloadAllMediaScores();
    downloadAllPlayerPrices();
}

execute();