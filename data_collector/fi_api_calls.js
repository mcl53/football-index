const secrets = require("./secrets");
const fetch = require("node-fetch");
const utils = require("./utils");

async function sendRequest(url, responseHandler, resHandlerArgs) {
   const params = {
       "Accept": "application/json; charset=utf-8",
       "x-access-token": secrets.x_access_token
   };

   try {
    const encodedUrl = encodeURI(url);
    console.log(`Sending request to ${url} at ${new Date().getTime()}`);

    let response = await fetch(encodedUrl, {headers: params, compress: false});
    let data = await response.json();
    
    await responseHandler(data, resHandlerArgs);
   } catch(err) {
    console.log(err);
   }
}

module.exports = {
    sendRequest: sendRequest
};