const fs = require("fs");
const secrets = require("./secrets");
const {writeToMediaScores, writeToPlayerData, updatePlayerData} = require("./mongo");
const utils = require("./utils");

async function saveMediaScores(json, dateStr) {

    let scoresList = [];

    json.items.forEach(player => {
        let playerObj = {
            name: player.name,
            urlname: player.urlname,
            score: player.score,
            scoreSell: player.scoreSell
        };

        scoresList.push(playerObj);
    });

    let obj = {
        date: dateStr,
        scores: scoresList
    };

    await utils.useDb(writeToMediaScores, obj);
}

function savePlayerPrices(json, playerName) {

    let playerPrices = [];

    json.days.forEach(price => {
        let pricesObj = {
            timestamp: price.timestamp,
            close: price.close
        };
        playerPrices.push(pricesObj);
    });

    let obj = {
        player_name: playerName,
        price_history: playerPrices
    };

    utils.useDb(updatePlayerData, {player_name: playerName}, obj);
}

module.exports = {
    saveMediaScores: saveMediaScores,
    savePlayerPrices: savePlayerPrices
};
