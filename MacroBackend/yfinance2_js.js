///////////////////// Start script below ???????????????????????
// require syntax (if your code base does not support imports)
const yahooFinance = require('yahoo-finance2').default; // NOTE the .default

// Reading input from stdin
let data = '';

process.stdin.on('data', chunk => {
    data += chunk;
});

process.stdin.on('end', async () => {
    // Parse the JSON data
    const searchstr = JSON.parse(data);

    // Use the yahooFinance.search function
    const results = await yahooFinance.search(searchstr);

    // Log the results
    //console.log(results.data);

    // Output the result
    process.stdout.write(JSON.stringify(results));
});