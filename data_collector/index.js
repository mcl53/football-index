const api = require("./fi_api_calls");
const handlers = require("./api_response_handlers");
const secrets = require("./secrets");

function getNewMediaScores() {
    const todaysDate = new Date();
    const day = String(todaysDate.getDate()).padStart(2, "0");
    const month = String(todaysDate.getMonth() + 1).padStart(2, "0");
    const year = String(todaysDate.getFullYear());
    const dateString = year + month + day;

    url = `${secrets.media_scores_endpoint}${dateString}${secrets.media_scores_extra_params}`;

    api.sendRequest(url, handlers.saveMediaScores, dateString);
}

