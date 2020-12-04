const { MongoClient } = require("mongodb");

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

async function useDb(dbCallback, ...callbackArgs){
    const uri = "mongodb://127.0.0.1:27017/";
 
    const client = new MongoClient(uri, {useUnifiedTopology: true});
 
    try {
        await client.connect();
        
        const db = client.db("football-index");

        await dbCallback(db, ...callbackArgs);
 
    } catch (e) {
        console.error(e);
    } finally {
        await client.close();
    }
}

module.exports = {
    dateToString: dateToString,
    sleep: sleep,
    useDb: useDb
};