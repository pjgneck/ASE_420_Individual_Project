const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');
const cors = require('cors');
const path = require('path');

const app = express();
const port = 3030;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true })); // to parse form data

// MongoDB Atlas connection
const uri = 'mongodb+srv://handler:Wt7bunOgYVQTOKfh@webapp.jfjk1cj.mongodb.net/TerminalCommand?retryWrites=true&w=majority';
const dbName = 'TerminalCommand';
let db;

MongoClient.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(client => {
    db = client.db(dbName);
    console.log(`Connected to MongoDB Atlas: ${dbName}`);
    app.listen(port, () => {
      console.log(`Server running on http://localhost:${port}`);
    });
  })
  .catch(err => console.error('MongoDB connection failed:', err));

app.get('/users', async (req, res) => {
  try {
    const users = await db.collection('users').find({}).toArray();
    res.json(users);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// Handle login
app.post('/login', async (req, res) => {
  const username = req.body.username?.trim();
  const password = req.body.password?.trim();

  if (!username || !password) {
    return res.status(400).json({ success: false, message: 'Username and password required' });
  }

  const user = await db.collection('users').findOne({ username, password });

  if (user) {
    res.json({
      success: true,
      username: username,
      token: user.token,
      commands: user.commands,
      devices: user.devices
    });
  } else {
    res.status(401).json({ success: false, message: 'Invalid username or password' });
  }
});

// POST /commands/import
app.post('/commands/import', async (req, res) => {
  const { token, commands } = req.body;

  if (!token || !Array.isArray(commands) || !commands.length) {
    return res.status(400).json({
      success: false,
      message: 'Token and an array of commands are required'
    });
  }

  try {
    const user = await db.collection('users').findOne({ token: token.trim() });

    if (!user) {
      return res.status(404).json({ success: false, message: 'Invalid token or user not found' });
    }

    // Generate IDs for imported commands
    const startingId = user.commands.length ? user.commands[user.commands.length - 1].id + 1 : 1;
    const importedCommands = commands.map((cmd, index) => ({
      id: startingId + index,
      last_used: cmd.last_used || new Date().toISOString().split('T')[0],
      command: cmd.command,
      description: cmd.description || ''
    }));

    // Add all commands to user
    await db.collection('users').updateOne(
      { token: token.trim() },
      { $push: { commands: { $each: importedCommands } } }
    );

    res.json({
      success: true,
      message: `${importedCommands.length} commands imported`,
      commands: importedCommands
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// POST /commands/import
app.post('/commands/import', async (req, res) => {
  const { token, commands } = req.body;

  if (!token || !Array.isArray(commands) || !commands.length) {
    return res.status(400).json({
      success: false,
      message: 'Token and an array of commands are required'
    });
  }

  try {
    const user = await db.collection('users').findOne({ token: token.trim() });

    if (!user) {
      return res.status(404).json({ success: false, message: 'Invalid token or user not found' });
    }

    // Generate IDs for imported commands
    const startingId = user.commands.length ? user.commands[user.commands.length - 1].id + 1 : 1;
    const importedCommands = commands.map((cmd, index) => ({
      id: startingId + index,
      last_used: cmd.last_used || new Date().toISOString().split('T')[0],
      command: cmd.command,
      description: cmd.description || ''
    }));

    // Add all commands to user
    await db.collection('users').updateOne(
      { token: token.trim() },
      { $push: { commands: { $each: importedCommands } } }
    );

    res.json({
      success: true,
      message: `${importedCommands.length} commands imported`,
      commands: importedCommands
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// POST /devices/add
app.post('/devices/add', async (req, res) => {
  const { token, device, ip } = req.body;

  if (!token || !device || !ip) {
    return res.status(400).json({
      success: false,
      message: 'Token, device, and IP are required'
    });
  }

  try {
    const user = await db.collection('users').findOne({ token: token.trim() });

    if (!user) {
      return res.status(404).json({ success: false, message: 'Invalid token or user not found' });
    }

    // Generate new device ID (string)
    const newId = user.devices.length ? (parseInt(user.devices[user.devices.length - 1].id) + 1).toString() : "1";

    const newDevice = {
      id: newId,
      device,
      ip
    };

    // Add device to user
    await db.collection('users').updateOne(
      { token: token.trim() },
      { $push: { devices: newDevice } }
    );

    res.json({ success: true, message: 'Device added', device: newDevice });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

app.get('/commands', async (req, res) => {
  const token = req.query.token?.trim();

  if (!token) {
    return res.status(400).json({ success: false, message: 'Token is required' });
  }

  try {
    const user = await db.collection('users').findOne({ token });

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    res.json({ success: true, commands: user.commands });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// GET /devices?token=USER_TOKEN
app.get('/devices', async (req, res) => {
  const token = req.query.token?.trim();

  if (!token) {
    return res.status(400).json({ success: false, message: 'Token is required' });
  }

  try {
    const user = await db.collection('users').findOne({ token });

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    res.json({ success: true, devices: user.devices });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});