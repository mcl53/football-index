const api = require("./fi_api_calls");
const mongoHandlers = require("./api_response_handlers_mongo");
const secrets = require("./secrets");
const utils = require("./utils");

let currentApiRequests = 0;

function todaysDateString() {
    const todaysDate = new Date();
    // Previous date is the latest info
    const yesterdaysDate = new Date(todaysDate.getFullYear(), todaysDate.getMonth(), (todaysDate.getDate() - 1)); 
    const dateString = dateToString(yesterdaysDate);

    return dateString;
}

function dateToString(date) {
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

async function getNewMediaScores(dateString, dbCallback) {
    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    await api.sendRequest(url, mongoHandlers.saveMediaScores, dateString);

    // Download new player data for the previous 2 days as this is used in model validation
    let year = parseInt(dateString.slice(0, 4));
    let month = parseInt(dateString.slice(4, 6));
    let day = parseInt(dateString.slice(6));

    let yesterday = new Date(year, month - 1, day - 1);
    let dayBefore = new Date(year, month - 1, day - 2);

    let yesterdayStr = dateToString(yesterday);
    let dayBeforeStr = dateToString(dayBefore);

    utils.useDb(dbCallback, dateString);
    utils.useDb(dbCallback, yesterdayStr);
    utils.useDb(dbCallback, dayBeforeStr);
}

async function updatePlayerPrices(playerName) {
    let url = `${secrets.price_history_endpoint}${playerName}`;

    currentApiRequests += 1;
    await utils.sleep(2000 * currentApiRequests);

    api.sendRequest(url, mongoHandlers.savePlayerPrices, playerName);
}

async function updateTodaysPlayers(db, dateString) {

    mediaScoresCollection = db.collection("media-scores");
    playersCollection = db.collection("players");

    mediaScores = await mediaScoresCollection.findOne({date: dateString});

    mediaScores.scores.forEach(score => {
        updatePlayerPrices(score.urlname);
    });
}

function execute() {
    const dateStr = todaysDateString();
    console.log(`Beginning script for ${dateStr}`);
    getNewMediaScores(dateStr, updateTodaysPlayers);
}

execute();
