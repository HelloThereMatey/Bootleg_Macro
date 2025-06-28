const yahooFinance = require('yahoo-finance2').default;

async function searchSymbols(searchTerm) {
    try {
        const results = await yahooFinance.search(searchTerm);
        const formattedResults = {
            quotes: results.quotes || [],
            news: results.news || []
        };
        console.log(JSON.stringify(formattedResults));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            operation: 'search',
            error: error.message,
            searchTerm: searchTerm,
            quotes: [],
            news: []
        }));
    }
}

async function fetchData(symbol, period1, period2, interval = '1d') {
    try {
        // Validate and convert timestamps
        const startDate = new Date(period1 * 1000);
        const endDate = new Date(period2 * 1000);
        
        // Validate the dates
        if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
            throw new Error('Invalid date timestamps provided');
        }
        
        if (startDate >= endDate) {
            throw new Error('Start date must be before end date');
        }
        
        const queryOptions = {
            period1: startDate,
            period2: endDate,
            interval: interval
        };

        console.error(`Fetching data for ${symbol} from ${startDate.toISOString()} to ${endDate.toISOString()} with interval ${interval}`);
        
        const result = await yahooFinance.historical(symbol, queryOptions);
        
        if (!result || result.length === 0) {
            throw new Error('No data returned from Yahoo Finance');
        }
        
        // Convert to format compatible with Python
        const data = result.map(item => ({
            Date: item.date.toISOString().split('T')[0],
            Open: item.open || null,
            High: item.high || null,
            Low: item.low || null,
            Close: item.close || null,
            Volume: item.volume || null,
            AdjClose: item.adjClose || item.close || null
        }));

        console.log(JSON.stringify({
            success: true,
            operation: 'fetch',
            data: data,
            symbol: symbol,
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0],
            interval: interval
        }));

    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            operation: 'fetch',
            error: error.message,
            symbol: symbol,
            data: []
        }));
    }
}

// Handle stdin input for search operations
async function handleStdinInput() {
    let input = '';
    
    process.stdin.on('data', (chunk) => {
        input += chunk;
    });
    
    process.stdin.on('end', async () => {
        try {
            const searchTerm = JSON.parse(input.trim());
            await searchSymbols(searchTerm);
        } catch (error) {
            console.log(JSON.stringify({
                success: false,
                error: `Invalid input: ${error.message}`,
                quotes: [],
                news: []
            }));
        }
    });
}

// Main execution logic
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        // No command line args, handle stdin input
        await handleStdinInput();
        return;
    }

    const operation = args[0].toLowerCase();

    switch (operation) {
        case 'search':
            if (args.length < 2) {
                console.log(JSON.stringify({
                    success: false,
                    error: "Search requires a search term. Usage: node script.js search <searchTerm>"
                }));
                return;
            }
            await searchSymbols(args[1]);
            break;

        case 'fetch':
            if (args.length < 4) {
                console.log(JSON.stringify({
                    success: false,
                    error: "Fetch requires symbol, start timestamp, and end timestamp. Usage: node script.js fetch <symbol> <startTimestamp> <endTimestamp> [interval]"
                }));
                return;
            }
            
            const symbol = args[1];
            const startTimestamp = parseInt(args[2]);
            const endTimestamp = parseInt(args[3]);
            const interval = args[4] || '1d';
            
            // Validate timestamps
            if (isNaN(startTimestamp) || isNaN(endTimestamp)) {
                console.log(JSON.stringify({
                    success: false,
                    error: "Invalid timestamps provided"
                }));
                return;
            }
            
            await fetchData(symbol, startTimestamp, endTimestamp, interval);
            break;

        default:
            console.log(JSON.stringify({
                success: false,
                error: `Unknown operation: ${operation}. Available operations: search, fetch`
            }));
    }
}

// Run main function
main().catch(error => {
    console.log(JSON.stringify({
        success: false,
        error: error.message
    }));
});