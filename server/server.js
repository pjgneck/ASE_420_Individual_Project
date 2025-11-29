// server.js

const express = require('express');
const cors = require('cors');
const { connectToMongo, dbMiddleware } = require('./db');
const authRoutes = require('./routes/authRoutes');
const dataRoutes = require('./routes/dataRoutes');

const app = express();
const port = 3030;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Apply database middleware to all requests that need it
app.use(dbMiddleware); 

// --- Route Handlers ---

// Base route for authentication (e.g., /login)
app.use('/', authRoutes);

// Protected routes for commands and devices
// These routes now require a token check internally
app.use('/', dataRoutes);


// --- Server Startup ---

// 1. Connect to MongoDB
connectToMongo()
    .then(() => {
        // 2. Start the Express server only after the DB connection is successful
        app.listen(port, () => {
            console.log(`Server running on http://localhost:${port}`);
        });
    })
    .catch((err) => {
        console.error("Application failed to start due to MongoDB connection error.");
        process.exit(1); // Exit process if database connection fails
    });