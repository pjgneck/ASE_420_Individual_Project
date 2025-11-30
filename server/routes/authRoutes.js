const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
import bcrypt from 'bcrypt';

/**
 * Utility function to generate a simple unique token.
 * In a real application, this should be a robust JWT or similar.
 */
const generateToken = () => {
    // Generate a simple UUID token for this example
    return uuidv4();
};

/**
 * GET /users
 * Fetches a list of all users. (Typically an Admin/Debug route)
 */
router.get('/users', async (req, res) => {
    try {
        const db = req.db; // Database object attached by middleware
        // NOTE: In a production application, sensitive data like passwords should never be returned, 
        // and this endpoint should be heavily restricted.
        const users = await db.collection('users').find({}).project({ password: 0 }).toArray();
        res.json(users);
    } catch (err) {
        console.error('Fetch Users Error:', err);
        res.status(500).json({ error: 'Failed to fetch users' });
    }
});

/**
 * POST /login
 * Authenticates the user and returns their token and initial data (commands, devices).
 */
router.post('/login', async (req, res) => {
    const username = req.body.username?.trim();
    const password = req.body.password?.trim();
    const db = req.db; // Database object attached by middleware

    if (!username || !password) {
        return res.status(400).json({ success: false, message: 'Username and password required' });
    }

    try {
        // Find the user by username and password
        const user = await db.collection('users').findOne({
            username,
            password // WARNING: Storing plain passwords is bad practice. Use bcrypt in production!
        });

        if (user) {
            // Success: Return necessary user data
            res.json({
                success: true,
                username: user.username,
                token: user.token,
                commands: user.commands || [], // Ensure commands array exists
                devices: user.devices || []     // Ensure devices array exists
            });
        } else {
            // Failure: Invalid credentials
            res.status(401).json({ success: false, message: 'Invalid username or password' });
        }
    } catch (err) {
        console.error('Login Error:', err);
        res.status(500).json({ success: false, message: 'Server error during login' });
    }
});

/**
 * POST /signup
 * Registers a new user account.
 */
router.post('/signup', async (req, res) => {
    const username = req.body.username?.trim();
    const password = req.body.password?.trim();
    const db = req.db;

    if (!username || !password) {
        return res.status(400).json({ success: false, message: 'Username and password required' });
    }

    if (username.length < 3) {
        return res.status(400).json({ success: false, message: 'Username must be at least 3 characters long' });
    }

    try {
        // 1. Check if user already exists
        const existingUser = await db.collection('users').findOne({ username });

        if (existingUser) {
            return res.status(409).json({ success: false, message: 'Username already taken' });
        }

        // 2. Hash the password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // 3. Create new user object
        const newUser = {
            username: username,
            password: hashedPassword, // password now hashed securely
            token: generateToken(),
            commands: [],
            devices: [],
            createdAt: new Date()
        };

        // 4. Insert into database
        const result = await db.collection('users').insertOne(newUser);

        // 5. Respond
        res.status(201).json({
            success: true,
            message: 'User registered successfully',
            username: newUser.username,
            token: newUser.token,
            userId: result.insertedId
        });

    } catch (err) {
        console.error('Signup Error:', err);
        res.status(500).json({ success: false, message: 'Server error during registration' });
    }
});

module.exports = router;