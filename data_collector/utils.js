const { MongoClient } = require("mongodb");

function dateToString(date) {
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear());
    const dateString = year + month + day;

    return dateString;
}

function datestrToDate(datestr) {
    const year = Number(datestr.slice(0, 4));
    const month = Number(datestr.slice(4, 6));
    const day = Number(datestr.slice(6));

    const date = new Date(year, month, day);

    return date;
}

function sleep(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

async function useDb(dbCallback, ...callbackArgs){
    const uri = "mongodb://127.0.0.1:27017/";
 
    const client = new MongoClient(uri, {useUnifiedTopology: true});

    let result
 
    try {

        await client.connect();
        
        const db = client.db("football-index");

        result = await dbCallback(db, ...callbackArgs);
 
    } catch (e) {

        console.error(e);

    } finally {

        await client.close();

        if (result) {
            return result;
        }

    }
    
}

module.exports = {
    dateToString: dateToString,
    sleep: sleep,
    useDb: useDb,
    datestrToDate: datestrToDate
};