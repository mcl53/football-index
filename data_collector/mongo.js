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

async function writeToMediaScores(db, object) {
    const mediaCollection = await db.collection("media-scores");
    let result = await mediaCollection.insertOne(object);
    if (result.insertedCount != 1) {
        console.log(result);
    }
}

async function writeToPlayerData(db, object) {
    const playersCollection = await db.collection("players");
    let result = await playersCollection.insertOne(object);
    if (result.ok != 1) {
        console.log(result);
    }
}

async function updatePlayerData(db, query, object) {
    const playersCollection = await db.collection("players");
    let result = await playersCollection.findOneAndUpdate(query, {$set: object}, {upsert: true});
    if (result.ok != 1) {
        console.log(result);
    }
}

if (require.main === module) {
    writeAllMediaScoresToDb();
    writeAllPlayerDataToDb();
}

module.exports = {
    writeToMediaScores: writeToMediaScores,
    writeToPlayerData: writeToPlayerData,
    updatePlayerData: updatePlayerData
};