const path = require('path');

// Get the CONDA_PREFIX environment variable
const condaPrefix = process.env.CONDA_PREFIX;
console.log(condaPrefix);

// If CONDA_PREFIX is set, construct the path to the package
if (condaPrefix) {
    const packagePath = path.join(condaPrefix, 'lib', 'node_modules', 'lib', 'node_modules', '@mathieuc', 'tradingview');
    const TradingView = require(packagePath);
    // Use the TradingView module as needed
} else {
    console.error('CONDA_PREFIX is not set. Please check your environment configuration.');
}


///////////////////// Start script below ???????????????????????
const fs = require('fs');
const TradingView = require('@mathieuc/tradingview');

// Reading input from stdin
let data = '';
process.stdin.on('data', chunk => {
    data += chunk;
});
    
console.log(data);
process.stdin.on('end', () => {
    // Parse the JSON data
    const obj = JSON.parse(data);

    // Suppose you're using a library to process this data
    const processedData = TradingView.searchMarket(search = obj).then((rs) => {
        const limitedResults = rs.slice(0, 30); // Adjust the number as needed
        console.log(limitedResults);
      });

    // Output the result
    process.stdout.write(JSON.stringify(processedData));
});