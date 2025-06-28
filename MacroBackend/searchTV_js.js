// const path = require('path');

// // Get the CONDA_PREFIX environment variable
// const condaPrefix = process.env.CONDA_PREFIX;
// console.log(condaPrefix);

// // If CONDA_PREFIX is set, construct the path to the package
// if (condaPrefix) {
//     const packagePath = path.join(condaPrefix, 'lib', 'node_modules', 'lib', 'node_modules', '@mathieuc', 'tradingview');
//     const TradingView = require(packagePath);
//     // Use the TradingView module as needed
// } else {
//     console.error('CONDA_PREFIX is not set. Please check your environment configuration.');
// }

///////////////////// Start script below ???????????????????????
const fs = require('fs');
const TradingView = require('@mathieuc/tradingview');

// Reading input from stdin
let data = '';
process.stdin.on('data', chunk => {
    data += chunk;
});

process.stdin.on('end', async () => {
    try {
        // Parse the JSON data
        const searchstr = JSON.parse(data.trim());
        
        // Use the TradingView library to search market
        const results = await TradingView.searchMarket(searchstr);
        const limitedResults = results.slice(0, 30);
        
        // Output the result as JSON
        console.log(JSON.stringify(limitedResults));
    } catch (error) {
        console.error(JSON.stringify({
            error: error.message,
            success: false
        }));
        process.exit(1);
    }
});