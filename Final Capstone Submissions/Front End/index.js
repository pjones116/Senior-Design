// written by Rachel Zaltz
function ignoreFavicon(req, res, next) {
    if (req.originalUrl === '/favicon.ico') {
        res.status(204).json({ nope: true });
    } else {
        next();
    }
}
var express = require('express'); var cors = require('cors');
var app = express();
var React = require('react'); app.use(ignoreFavicon); app.use(cors());
app.get('/', function (req, res) {
    var sql = require("mssql");
    // config for your database 
    var config = {
        server: 'X.X.X.X', user: 'XXXX',
        port: XXXX,
        password: 'XXXX', database: 'XXXX'
    };
    // connect to your database 
    sql.connect(config, function (err) {
        if (err) console.log(err);
        // create Request object
        var request = new sql.Request();
        // query to the database and get the records
        request.query('select * from XXXX.XXXX.XXXX', function (err, recordset) {
            if (err) console.log(err)
            // send records as a response 
            res.send(recordset);
        });
    });
});

// Listen on a specific host via the HOST environment variable 
var host = process.env.HOST || 'localhost';
// Listen on a specific port via the PORT environment variable 
var port = process.env.PORT || 5000;
var cors_proxy = require('cors-anywhere'); cors_proxy.createServer({
    originWhitelist: [],
    // Allow all origins 
    requireHeader: ['origin', 'x-requested-with'], removeHeaders: ['cookie', 'cookie2']
}).listen(port, host, function () {
    console.log('Running CORS Anywhere on ' + host + ':' + port);
});
var server = app.listen(5000, function () {
    console.log('Server is running..');
});