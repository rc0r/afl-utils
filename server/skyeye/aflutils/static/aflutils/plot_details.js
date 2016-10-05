function getDate(timestamp)
{
    var date = new Date(timestamp * 1000);

    var year = date.getUTCFullYear();
    var month = date.getUTCMonth() + 1; // getMonth() is zero-indexed, so we'll increment to get the correct month number
    var day = date.getUTCDate();
    var hours = date.getUTCHours();
    var minutes = date.getUTCMinutes();
    var seconds = date.getUTCSeconds();

    month = (month < 10) ? '0' + month : month;
    day = (day < 10) ? '0' + day : day;
    hours = (hours < 10) ? '0' + hours : hours;
    minutes = (minutes < 10) ? '0' + minutes : minutes;
    seconds = (seconds < 10) ? '0' + seconds: seconds;

    return month + '-' + day + ' ' + hours + ':' + minutes;
}

var times = last_update;

for(i=0; i<last_update.length; i++) {
    times[i] = getDate(last_update[i])
}

var data_paths = {
    labels: times,
    datasets: [
        {
            label: "Pending total",
            fill: true,
            lineTension: 0.1,
            backgroundColor: "rgba(183,191,74,0.4)", //  "rgba(75,192,192,0.4)",
            borderColor: "rgba(183,191,74,1)", // "rgba(75,192,192,1)",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(183,191,74,1)", // "rgba(75,192,192,1)",
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(183,191,74,1)", // rgba(75,192,192,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: pending_total,
            spanGaps: false
        },
        {
            label: "Pending favs",
            fill: true,
            lineTension: 0.1,
            backgroundColor: "rgba(191,171,74,0.4)",
            borderColor: "rgba(191,171,74,1)",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(191,171,74,1)",
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(191,171,74,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: pending_favs,
            spanGaps: false
        }
    ]
};

var data_crashes = {
    labels: times,
    datasets: [
        {
            label: "Unique Crashes",
            fill: true,
            lineTension: 0.1,
            backgroundColor: "rgba(191,95,74,0.4)", //  "rgba(75,192,192,0.4)",
            borderColor: "rgba(191,95,74,1)", // "rgba(75,192,192,1)",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(191,95,74,1)", // "rgba(75,192,192,1)",
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(191,95,74,1)", // rgba(75,192,192,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: unique_crashes,
            spanGaps: false
        },
        {
            label: "Unique Hangs",
            fill: true,
            lineTension: 0.1,
            backgroundColor: "rgba(191,74,111,0.4)",
            borderColor: "rgba(191,74,111,1)",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(191,74,111,1)",
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(191,74,111,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: unique_hangs,
            spanGaps: false
        }
    ]
};

var options = {
    responsive: false
};

var ctx_paths = document.getElementById("graph_paths").getContext("2d");
ctx_paths.canvas.width = 600;
ctx_paths.canvas.height = 300;

var myLineChart_paths = new Chart(ctx_paths, {
    type: 'line',
    data: data_paths,
    options: options
});

var ctx_crashes = document.getElementById("graph_crashes").getContext("2d");
ctx_crashes.canvas.width = 600;
ctx_crashes.canvas.height = 300;

var myLineChart_crashes = new Chart(ctx_crashes, {
    type: 'line',
    data: data_crashes,
    options: options
});
