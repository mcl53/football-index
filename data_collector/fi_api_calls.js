const secrets = require("./secrets");
const fetch = require("node-fetch")
const fs = require("fs");

currentApiCalls = 100;
firstCall = 0;

async function sendRequest(url, responseFunc) {
    /* Check to see if max API calls have been reached first.
    If we have, wait until at least 1 minute after to make another 100.
    Do this first because here we set API calls to 0 and then next get the start time for the next 100.
    */
   if (currentApiCalls == 100) {
       currentApiCalls = 0;
       let lastCall = (new Date().getTime()) / 1000;
       while (lastCall < firstCall) {
           lastCall = (new Date().getTime()) / 1000;
       }
   }

   if (currentApiCalls == 0) {
       firstCall = (new Date().getTime()) / 1000;
   }

   currentApiCalls += 1;

   const params = {
       "Accept": "application/json",
       "x-access-token": secrets.x_access_token
   };
   try {
    let response = await fetch(url, {headers: params});
    let data = await response.json();
    responseFunc(data, Object.values(arguments).slice(2));
   } catch(err) {
    console.log(err);
    return;
   }   
}

function testPromiseResponse(res) {
    console.log(res);
}

function jsonToCsv(json, headers) {
    /* This function expects to be passed a number of additional arguments greater than 1, 
    where each argument is the name of a column header for the csv file */

    // All json from this API contains data within an object assigned to the key 'items'
    const listOfObjects = json.items;
    
    let toCsv = headers.join(",");

    /* Parse the data provided into rows. The column headers must be the names of keys in each object of the listOfObjects.
    Here we iterate through each obj in the listOfObjects and create a new row in the csv with each value chosen separated by a comma*/
    listOfObjects.forEach(obj => {
        toCsv += "\r\n";
        let newLine = headers.map(header => {
            return `${obj[header]}`;
        });
        toCsv += newLine.join(",")
        toCsv.slice(0, -1);
    });
    console.log(toCsv);
    fs.writeFile("./test.csv", toCsv, (err, written) => {
        if (err) {
            console.log(err);
            return;
        } else {
            console.log(`Bytes written: ${written}`);
        }
    });
}

sendRequest(`${secrets.media_scores_endpoint}20200701${secrets.media_scores_extra_params}`, jsonToCsv, "name", "score");

