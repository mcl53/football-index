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

module.exports = {
    dateToString: dateToString,
    sleep: sleep
};