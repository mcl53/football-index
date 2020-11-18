const secrets = require("./secrets");
const fs = require("fs");
const csv = require("csv-parser");
const { MongoClient } = require("mongodb");

async function useDb(dbCallback){
    const uri = "mongodb://127.0.0.1:27017/";
 

    const client = new MongoClient(uri, {useUnifiedTopology: true});
 
    try {
        await client.connect();
 
        await dbCallback(client);
 
    } catch (e) {
        console.error(e);
    } finally {
        await client.close();
    }
}

async function listDatabases(client){
    databasesList = await client.db().admin().listDatabases();
 
    console.log("Databases:");
    databasesList.databases.forEach(db => console.log(` - ${db.name}`));
};

useDb(listDatabases);

