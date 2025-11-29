
const express = require('express');
const router = express.Router();

/**
 * Middleware to check for a valid token and attach the user object to the request.
 * * FIX: Added optional chaining (?. ) to req.body and req.query to prevent the
 * "Cannot read properties of undefined (reading 'token')" TypeError.
 */
const checkToken = async (req, res, next) => {
    // Safely check token from body, query, or headers using optional chaining
    const token = (req.body?.token || req.query?.token || req.headers['x-access-token'])?.trim();

    if (!token) {
        return res.status(401).json({ success: false, message: 'Access Token is required' });
    }

    try {
        const user = await req.db.collection('users').findOne({ token });
        if (!user) {
            return res.status(404).json({ success: false, message: 'Invalid token or user not found' });
        }
        req.user = user; // Attach user object to request
        next();
    } catch (err) {
        console.error('Token validation error:', err);
        res.status(500).json({ success: false, message: 'Server error during token validation' });
    }
};

// Apply token check to all routes in this file
router.use(checkToken);

// ================= COMMANDS CRUD =================

// C: CREATE - Add Single Command
router.post('/commands/add', async (req, res) => {
    const { command, description } = req.body;
    const db = req.db;
    const user = req.user;

    if (!command) {
        return res.status(400).json({ success: false, message: 'Command text is required' });
    }

    try {
        // Determine the next ID based on existing commands
        const lastCommand = user.commands.length > 0 ? user.commands[user.commands.length - 1] : { id: 0 };
        // Use an integer ID for easier sorting/comparison
        const newId = parseInt(lastCommand.id) + 1; 

        const newCommand = {
            id: newId,
            command: command,
            description: description || '',
            last_used: new Date().toISOString().split('T')[0]
        };

        await db.collection('users').updateOne(
            { _id: user._id },
            { $push: { commands: newCommand } }
        );

        res.json({ success: true, message: 'Command added', command: newCommand });
    } catch (err) {
        console.error('Command Add Error:', err);
        res.status(500).json({ success: false, message: 'Server error during command addition' });
    }
});

// R: READ - Get All Commands
router.get('/commands', (req, res) => {
    res.json({ success: true, commands: req.user.commands || [] });
});

// U: UPDATE - Update Command details by ID
router.put('/commands/update', async (req, res) => {
    // Requires the ID to identify the item, and fields to update (command, description)
    const { id, command, description, last_used } = req.body; 
    const db = req.db;
    const user = req.user;

    // The ID must be an integer, as we are storing it as a number
    const commandId = parseInt(id); 

    if (!commandId) {
        return res.status(400).json({ success: false, message: 'Command ID is required for update' });
    }

    try {
        const updateFields = {};
        if (command) updateFields['commands.$.command'] = command;
        if (description !== undefined) updateFields['commands.$.description'] = description;
        if (last_used) updateFields['commands.$.last_used'] = last_used; 
        
        if (Object.keys(updateFields).length === 0) {
            return res.status(400).json({ success: false, message: 'No fields provided for update' });
        }

        const result = await db.collection('users').updateOne(
            // 1. Find the user AND the command within the array
            { _id: user._id, 'commands.id': commandId }, 
            // 2. Use the positional operator ($) to update the matched element
            { $set: updateFields }
        );

        if (result.modifiedCount === 0) {
            return res.status(404).json({ success: false, message: 'Command not found or no change applied' });
        }

        res.json({ success: true, message: `Command ID ${commandId} updated successfully` });
    } catch (err) {
        console.error('Command Update Error:', err);
        res.status(500).json({ success: false, message: 'Server error during command update' });
    }
});

// D: DELETE - Remove Command by ID
router.delete('/commands/remove', async (req, res) => {
    // We will use the ID for the most reliable removal
    const { id } = req.body;
    const db = req.db;
    const user = req.user;
    
    const commandId = parseInt(id);

    if (!commandId) {
        return res.status(400).json({ success: false, message: 'Command ID is required for removal' });
    }

    try {
        // Use $pull to remove the item matching the ID from the array
        const result = await db.collection('users').updateOne(
            { _id: user._id },
            { $pull: { commands: { id: commandId } } }
        );

        if (result.modifiedCount === 0) {
            return res.status(404).json({ success: false, message: 'Command not found or already removed' });
        }

        res.json({ success: true, message: `Command ID ${commandId} removed successfully` });
    } catch (err) {
        console.error('Command Remove Error:', err);
        res.status(500).json({ success: false, message: 'Server error during command removal' });
    }
});


// Handler for bulk imports (maintained for completeness)
router.post('/commands/import', async (req, res) => {
    const { commands } = req.body;
    const db = req.db;
    const user = req.user;

    if (!Array.isArray(commands) || !commands.length) {
        return res.status(400).json({ success: false, message: 'An array of commands is required' });
    }

    try {
        const lastCommand = user.commands.length > 0 ? user.commands[user.commands.length - 1] : { id: 0 };
        const startingId = parseInt(lastCommand.id) + 1;

        const importedCommands = commands.map((cmd, index) => ({
            id: startingId + index,
            last_used: cmd.last_used || new Date().toISOString().split('T')[0],
            command: cmd.command,
            description: cmd.description || ''
        }));

        await db.collection('users').updateOne(
            { _id: user._id },
            { $push: { commands: { $each: importedCommands } } }
        );

        res.json({ success: true, message: `${importedCommands.length} commands imported`, commands: importedCommands });
    } catch (err) {
        console.error('Command Import Error:', err);
        res.status(500).json({ success: false, message: 'Server error during command import' });
    }
});


// ================= DEVICES CRUD =================

// C: CREATE - Add Single Device
router.post('/devices/add', async (req, res) => {
    const { device, ip } = req.body;
    const db = req.db;
    const user = req.user;

    if (!device || !ip) {
        return res.status(400).json({ success: false, message: 'Device name and IP are required' });
    }

    try {
        // Generate new device ID (assuming your existing IDs are strings)
        const lastDevice = user.devices.length > 0 ? user.devices[user.devices.length - 1] : { id: "0" };
        const newId = (parseInt(lastDevice.id) + 1).toString();

        const newDevice = {
            id: newId,
            device,
            ip
        };

        await db.collection('users').updateOne(
            { _id: user._id },
            { $push: { devices: newDevice } }
        );

        res.json({ success: true, message: 'Device added', device: newDevice });
    } catch (err) {
        console.error('Device Add Error:', err);
        res.status(500).json({ success: false, message: 'Server error during device addition' });
    }
});

// R: READ - Get All Devices
router.get('/devices', (req, res) => {
    res.json({ success: true, devices: req.user.devices || [] });
});


// U: UPDATE - Update Device details by ID
router.put('/devices/update', async (req, res) => {
    // Requires the ID to identify the item, and fields to update (device, ip)
    const { id, device, ip } = req.body; 
    const db = req.db;
    const user = req.user;

    const deviceId = id ? id.toString() : null;

    if (!deviceId) {
        return res.status(400).json({ success: false, message: 'Device ID is required for update' });
    }

    try {
        const updateFields = {};
        if (device) updateFields['devices.$.device'] = device;
        if (ip) updateFields['devices.$.ip'] = ip;
        
        if (Object.keys(updateFields).length === 0) {
            return res.status(400).json({ success: false, message: 'No fields provided for update' });
        }

        const result = await db.collection('users').updateOne(
            { _id: user._id, 'devices.id': deviceId }, 
            { $set: updateFields }
        );

        if (result.modifiedCount === 0) {
            return res.status(404).json({ success: false, message: 'Device not found or no change applied' });
        }

        res.json({ success: true, message: `Device ID ${deviceId} updated successfully` });
    } catch (err) {
        console.error('Device Update Error:', err);
        res.status(500).json({ success: false, message: 'Server error during device update' });
    }
});


// D: DELETE - Remove Device by ID
router.delete('/devices/remove', async (req, res) => {
    const { id } = req.body;
    const db = req.db;
    const user = req.user;

    const deviceId = id ? id.toString() : null;

    if (!deviceId) {
        return res.status(400).json({ success: false, message: 'Device ID is required for removal' });
    }

    try {
        // Use $pull to remove the item matching the ID from the array
        const result = await db.collection('users').updateOne(
            { _id: user._id },
            { $pull: { devices: { id: deviceId } } }
        );

        if (result.modifiedCount === 0) {
            return res.status(404).json({ success: false, message: 'Device not found or already removed' });
        }

        res.json({ success: true, message: `Device ID ${deviceId} removed successfully` });
    } catch (err) {
        console.error('Device Remove Error:', err);
        res.status(500).json({ success: false, message: 'Server error during device removal' });
    }
});


module.exports = router;