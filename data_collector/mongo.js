const secrets = require("./secrets");
const utils = require("./utils");
const fs = require("fs");
const csv = require("csv-parser");

let current_connections = 0;

async function listDatabases(client) {
    databasesList = await client.db().admin().listDatabases();
 
    console.log("Databases:");
    databasesList.databases.forEach(db => console.log(` - ${db.name}`));
}

async function testWrite(db) {
    const testObj = {player_name: "mr-smith", score: 630};
    const mediaCol = await db.collection("media-scores");
    const result = await mediaCol.insertOne(testObj);
    console.log(result);
}

function writeAllMediaScoresToDb() {
    const todaysDate = new Date();
    const yesterdaysDate = todaysDate.setDate(todaysDate.getDate() - 1);

    let currentDate = secrets.firstMediaDate;

    const mediaBasePath = `${secrets.basePath}/media_scores/`;

    while (currentDate <= yesterdaysDate) {
        let dateStr = utils.dateToString(currentDate);
        let path = mediaBasePath + dateStr + ".csv";

        let dataFromFile = [];
        
        fs.createReadStream(path)
            .pipe(csv())
            .on("data", row => {
                dataFromFile.push(row);
            })
            .on("end", async () => {
                let obj = {
                    date: dateStr,
                    scores: dataFromFile
                };
                current_connections += 1;
                await utils.sleep(10 * current_connections);
                await utils.useDb(writeToMediaScores, obj);
            });
        
        currentDate.setDate(currentDate.getDate() + 1);
    }
}

function writeAllPlayerDataToDb() {
    fs.readdir(`${secrets.basePath}/player_prices`, (err, files) => {
        if (err) {
            console.error(err);
        } else {
            files.forEach(file => {
                writePlayerDataFile(file);
            });
        }
    });
}

function writePlayerDataFile(filename) {
    const fullPath = `${secrets.basePath}/player_prices/${filename}`;

    const playerName = filename.split(".")[0];

    let rows = [];

    fs.createReadStream(fullPath)
        .pipe(csv())
        .on("data", row => {
            rows.push(row);
        })
        .on("end", async () => {
            let obj = {
                player_name: playerName,
                price_history: rows
            };
            current_connections += 1;
            await utils.sleep(10 * current_connections);
            await utils.useDb(writeToPlayerData, obj);
        });
}

async function crossData() {
    let mediaScores = await utils.useDb(getMediaDataForCross);
    let players = await utils.useDb(getPlayerDataForCross);

    let writeData = []
    
    mediaScores.forEach(day => {
        let obj = {date: day.date, data: []}
        let timestamp = utils.datestrToDate(day.date).getTime();
        day.scores.forEach(playerScore => {
            let player_prices = players.find(player => player.player_name = playerScore.urlname);
            let playerObj = {
                start_price: player_prices.price_history.find(time => time = timestamp).close,
                end_price: player_prices.price_history.find(time => time = timestamp + 86400000).close,
                media_score: playerScore.score,
                "24h": player_prices.price_history.find(time => time = timestamp + 86400000 * 2).close,
                "48h": player_prices.price_history.find(time => time = timestamp + 86400000 * 3).close
            };

            obj.data.push(playerObj);
        });
        writeData.push(obj);
    });
    utils.useDb(writeAllTrainingData, writeData);
}

async function writeToMediaScores(db, obj) {
    const mediaCollection = await db.collection("media-scores");
    let result = await mediaCollection.insertOne(obj);
    if (result.insertedCount != 1) {
        console.log(result);
    }
}

async function writeToPlayerData(db, obj) {
    const playersCollection = await db.collection("players");
    let result = await playersCollection.insertOne(obj);
    if (result.ok != 1) {
        console.log(result);
    }
}

async function writeToTrainingData(db, obj) {
    const trainingCollection = await db.collection("training-data");
    let result = await trainingCollection.insertOne(obj);
    if (result.ok != 1) {
        console.log(result);
    }
}

async function writeAllTrainingData(db, arr) {
    const trainingCollection = await db.collection("training-data");
    let result = await trainingCollection.insertMany(arr);
    if (result.result.ok != 1) {
        console.log(result);
    }
}

async function updatePlayerData(db, query, obj) {
    const playersCollection = await db.collection("players");
    let result = await playersCollection.findOneAndUpdate(query, {$set: obj}, {upsert: true});
    if (result.ok != 1) {
        console.log(result);
    }
}

async function getMediaDataForCross(db) {
    const mediaCollection = await db.collection("media-scores");
    const cursor = await mediaCollection.find({}, {_id: 0, "scores.name": 0, "scores.scoreSell": 0});
    const result = await cursor.toArray();
    
    return result;
}

async function getPlayerDataForCross(db) {
    const playerCollection = await db.collection("players");
    const cursor = await playerCollection.find({}, {_id: 0});
    const result = await cursor.toArray();

    return result;
}

if (require.main === module) {
    writeAllMediaScoresToDb();
    writeAllPlayerDataToDb();
    crossData();
}

module.exports = {
    writeToMediaScores: writeToMediaScores,
    writeToPlayerData: writeToPlayerData,
    updatePlayerData: updatePlayerData,
    writeToTrainingData: writeToTrainingData
};