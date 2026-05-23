import json
import os
import time
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    # Economy methods
    def get_balance(self, user_id: int) -> int:
        """Get user balance from config"""
        return self.config.get("economy", {}).get("balances", {}).get(str(user_id), 0)
    
    def set_balance(self, user_id: int, amount: int):
        """Set user balance in config"""
        if "economy" not in self.config:
            self.config["economy"] = {}
        if "balances" not in self.config["economy"]:
            self.config["economy"]["balances"] = {}
        self.config["economy"]["balances"][str(user_id)] = amount
        self.save_config()
    
    def add_balance(self, user_id: int, amount: int) -> int:
        """Add to user balance and return new balance"""
        current = self.get_balance(user_id)
        new_balance = current + amount
        self.set_balance(user_id, new_balance)
        return new_balance
    
    def get_last_daily(self, user_id: int) -> int:
        """Get timestamp of user's last daily claim"""
        return self.config.get("economy", {}).get("last_daily", {}).get(str(user_id), 0)
    
    def set_last_daily(self, user_id: int, timestamp: int):
        """Set timestamp of user's last daily claim"""
        if "economy" not in self.config:
            self.config["economy"] = {}
        if "last_daily" not in self.config["economy"]:
            self.config["economy"]["last_daily"] = {}
        self.config["economy"]["last_daily"][str(user_id)] = timestamp
        self.save_config()
    
    def can_claim_daily(self, user_id: int) -> tuple:
        """Check if user can claim daily reward. Returns (can_claim, remaining_seconds)"""
        last_claim = self.get_last_daily(user_id)
        current_time = int(time.time())
        cooldown_seconds = 86400  # 24 hours
        
        if last_claim == 0:
            return True, 0
        
        elapsed = current_time - last_claim
        if elapsed >= cooldown_seconds:
            return True, 0
        else:
            return False, cooldown_seconds - elapsed
    
    # Leaderboard methods
    def get_leaderboard_data(self) -> Dict[str, Any]:
        """Get leaderboard data from config"""
        return self.config.get("leaderboard", {})
    
    def set_leaderboard_data(self, data: Dict[str, Any]):
        """Set leaderboard data in config"""
        self.config["leaderboard"] = data
        self.save_config()
    
    def get_guild_leaderboard(self, guild_id: str) -> Dict[str, Any]:
        """Get leaderboard data for a specific guild"""
        return self.config.get("leaderboard", {}).get(guild_id, {})
    
    def set_guild_leaderboard(self, guild_id: str, data: Dict[str, Any]):
        """Set leaderboard data for a specific guild"""
        if "leaderboard" not in self.config:
            self.config["leaderboard"] = {}
        self.config["leaderboard"][guild_id] = data
        self.save_config()
    
    def get_user_leaderboard_data(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get specific user's leaderboard data"""
        guild_data = self.get_guild_leaderboard(guild_id)
        return guild_data.get(user_id, {"username": "Unknown", "messages": 0})
    
    def set_user_leaderboard_data(self, guild_id: str, user_id: str, data: Dict[str, Any]):
        """Set specific user's leaderboard data"""
        guild_data = self.get_guild_leaderboard(guild_id)
        guild_data[user_id] = data
        self.set_guild_leaderboard(guild_id, guild_data)
    
    def increment_user_messages(self, guild_id: str, user_id: str, username: str):
        """Increment message count for a user"""
        user_data = self.get_user_leaderboard_data(guild_id, user_id)
        user_data["username"] = username  # Update username in case it changed
        user_data["messages"] = user_data.get("messages", 0) + 1
        self.set_user_leaderboard_data(guild_id, user_id, user_data)
    
    # ── Inventory (stored in config.json) ────────────────────────────
    _INV_KEY = "economy"          # nests under config["economy"]["inventories"]

    def get_inventory(self, user_id: int) -> dict:
        """Return {item_name: [base_value, ...], ...} for a user from config.json"""
        uid = str(user_id)
        inv_section = self.config.get(self._INV_KEY, {}).get("inventories", {})
        return dict(inv_section.get(uid, {}))

    def add_to_inventory(self, user_id: int, item_name: str, base_value: int):
        """Append one fish entry to a user's inventory in config.json"""
        uid = str(user_id)
        if self._INV_KEY not in self.config:
            self.config[self._INV_KEY] = {}
        if "inventories" not in self.config[self._INV_KEY]:
            self.config[self._INV_KEY]["inventories"] = {}
        if uid not in self.config[self._INV_KEY]["inventories"]:
            self.config[self._INV_KEY]["inventories"][uid] = {}
        user_inv = self.config[self._INV_KEY]["inventories"][uid]
        user_inv.setdefault(item_name, []).append(base_value)
        self.save_config()

    def remove_from_inventory(self, user_id: int, item_name: str, count: int = None):
        """Remove `count` entries of `item_name` from a user's inventory in config.json.
        If count is None, removes the entire item entry."""
        uid = str(user_id)
        inv_section = self.config.get(self._INV_KEY, {}).get("inventories", {})
        user_inv = inv_section.get(uid, {})
        if item_name not in user_inv:
            return []
        if count is None:
            removed = list(user_inv[item_name])
            del user_inv[item_name]
        else:
            removed = user_inv[item_name][:count]
            user_inv[item_name] = user_inv[item_name][count:]
            if not user_inv[item_name]:
                del user_inv[item_name]
        if not user_inv:
            inv_section.pop(uid, None)
        self.save_config()
        return removed

    # ── Log channel methods ─────────────────────────────────────────
    def get_log_channel(self, guild_id: str) -> str:
        """Get log channel for a guild"""
        return self.config.get("log_channels", {}).get(str(guild_id))
    
    def set_log_channel(self, guild_id: str, channel_id: str):
        """Set log channel for a guild"""
        if "log_channels" not in self.config:
            self.config["log_channels"] = {}
        self.config["log_channels"][str(guild_id)] = str(channel_id)
        self.save_config()

    # ── Welcome / Leave per-guild settings ──────────────────────────
    _WELCOME_LEAVE_KEY = "welcome_leave"
    _FIELD_CHANNEL  = "channel_id"
    _FIELD_MESSAGE  = "message"

    def _welcome_leave_section(self):
        """Return (and create if absent) the welcome_leave store in config.json."""
        key = self._WELCOME_LEAVE_KEY
        if key not in self.config:
            self.config[key] = {}
        return self.config[key]

    def set_welcome_channel(self, guild_id: str, channel_id: str):
        """Store the welcome channel ID for a guild"""
        section = self._welcome_leave_section()
        gid = str(guild_id)
        if gid not in section:
            section[gid] = {}
        section[gid][self._FIELD_CHANNEL] = str(channel_id)
        self.save_config()

    def get_welcome_channel(self, guild_id: str):
        """Return the registered welcome channel ID (str) or None"""
        return self.config.get(self._WELCOME_LEAVE_KEY, {}).get(str(guild_id), {}).get(self._FIELD_CHANNEL)

    def set_welcome_message(self, guild_id: str, message: str):
        """Store the custom welcome message for a guild"""
        section = self._welcome_leave_section()
        gid = str(guild_id)
        if gid not in section:
            section[gid] = {}
        section[gid][self._FIELD_MESSAGE] = message
        self.save_config()

    def get_welcome_message(self, guild_id: str):
        """Return the custom welcome message or None"""
        return self.config.get(self._WELCOME_LEAVE_KEY, {}).get(str(guild_id), {}).get(self._FIELD_MESSAGE)

    def set_leave_channel(self, guild_id: str, channel_id: str):
        """Store the leave/member-remove channel ID for a guild"""
        section = self._welcome_leave_section()
        gid = str(guild_id)
        if gid not in section:
            section[gid] = {}
        section[gid]["leave_channel_id"] = str(channel_id)
        self.save_config()

    def get_leave_channel(self, guild_id: str):
        """Return the registered leave channel ID (str) or None"""
        return self.config.get(self._WELCOME_LEAVE_KEY, {}).get(str(guild_id), {}).get("leave_channel_id")

    def set_leave_message(self, guild_id: str, message: str):
        """Store the custom leave/goodbye message for a guild"""
        section = self._welcome_leave_section()
        gid = str(guild_id)
        if gid not in section:
            section[gid] = {}
        section[gid]["leave_message"] = message
        self.save_config()

    def get_leave_message(self, guild_id: str):
        """Return the custom leave message or None"""
        return self.config.get(self._WELCOME_LEAVE_KEY, {}).get(str(guild_id), {}).get("leave_message")

# Global instance
config_manager = ConfigManager()
