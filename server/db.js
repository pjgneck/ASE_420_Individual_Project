// db.js

const { MongoClient } = require('mongodb');

// NOTE: Hardcoding credentials is a security risk. Use environment variables (process.env) instead!
const uri = '<MOngoDBLink>';
const dbName = 'commandBase';

let db;

/**
 * Connects to MongoDB Atlas and stores the database object.
 * @returns {Promise<Object>} The connected database object.
 */
async function connectToMongo() {
    if (db) {
        return db; // Return existing connection if available
    }

    try {
        const client = await MongoClient.connect(uri, { 
            useNewUrlParser: true, 
            useUnifiedTopology: true 
        });
        db = client.db(dbName);
        console.log(`Connected to MongoDB Atlas: ${dbName}`);
        return db;
    } catch (err) {
        console.error('MongoDB connection failed:', err);
        // Optionally re-throw to stop the server from starting
        throw err; 
    }
}

/**
 * Middleware function to ensure the database object is attached to the request.
 * Should be called after connectToMongo has succeeded.
 */
const dbMiddleware = (req, res, next) => {
    if (!db) {
        return res.status(503).json({ success: false, message: 'Database not connected' });
    }
    req.db = db;
    next();
};

module.exports = { 
    connectToMongo,
    dbMiddleware,
};