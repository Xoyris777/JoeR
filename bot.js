const { Client, GatewayIntentBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = './data.json';

// Initialize client with required intents
const client = new Client({ 
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ] 
});

// Load or initialize data
let data = {};
if (fs.existsSync(path)) {
  const rawData = fs.readFileSync(path);
  data = JSON.parse(rawData);
} else {
  // Create empty data file if it doesn't exist
  fs.writeFileSync(path, JSON.stringify({}, null, 2));
}

// Save data to file
function saveData() {
  fs.writeFileSync(path, JSON.stringify(data, null, 2));
}

// Handle incoming messages
client.on('messageCreate', (message) => {
  // Ignore bot messages and DMs
  if (message.author.bot || !message.guild) return;

  const guildId = message.guild.id;
  const userId = message.author.id;
  const username = message.author.username;

  // Initialize guild data if not exists
  if (!data[guildId]) {
    data[guildId] = {};
  }

  // Initialize user data if not exists
  if (!data[guildId][userId]) {
    data[guildId][userId] = { username: username, messages: 0 };
  } else {
    // Update username in case it changed
    data[guildId][userId].username = username;
  }

  // Increment message count
  data[guildId][userId].messages++;

  // Auto-save after each message update
  saveData();
});

// Handle .leaderboard command
client.on('messageCreate', (message) => {
  if (message.content === '.leaderboard' && !message.author.bot && message.guild) {
    const guildId = message.guild.id;
    
    // Check if server has any data
    if (!data[guildId] || Object.keys(data[guildId]).length === 0) {
      return message.reply('No leaderboard data found for this server.');
    }

    // Get users and sort by message count (descending)
    const users = Object.entries(data[guildId])
      .map(([userId, userData]) => ({
        userId,
        username: userData.username,
        messages: userData.messages
      }))
      .sort((a, b) => b.messages - a.messages)
      .slice(0, 10); // Top 10

    // Create embed
    const embed = new EmbedBuilder()
      .setColor('#0099ff')
      .setTitle(`🏆 ${message.guild.name} Leaderboard`)
      .setDescription(
        users.map((user, index) => 
          `${index + 1}. ${user.username} — ${user.messages} messages`
        ).join('\n') || 'No data available'
      )
      .setTimestamp()
      .setFooter({ text: 'Message counts updated in real-time' });

    message.reply({ embeds: [embed] });
  }
});

// Login to Discord
client.login(process.env.TOKEN); // Token should be set in environment variables