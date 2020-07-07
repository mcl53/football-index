const secrets = require("./secrets");
const fetch = require("node-fetch")

currentApiCalls = 100;
firstCall = 0;

async function sendRequest(url, responseHandler, resHandlerArgs) {
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
    responseHandler(data, resHandlerArgs);
   } catch(err) {
    console.log(err);
    return;
   }   
}

function testPromiseResponse(res) {
    console.log(res);
}

sendRequest(`${secrets.media_scores_endpoint}20200701${secrets.media_scores_extra_params}`, jsonToCsv, ["name", "score"]);
