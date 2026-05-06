from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    name: str
    description: str


PERMISSIONS: tuple[PermissionSeed, ...] = (
    PermissionSeed("users.read", "Read Users", "View user records"),
    PermissionSeed("users.create", "Create Users", "Create tenant users"),
    PermissionSeed("users.update", "Update Users", "Update user data"),
    PermissionSeed("users.delete", "Delete Users", "Delete users"),
    PermissionSeed("users.create_admin", "Create Admin Users", "Create tenant admin users"),
    PermissionSeed("users.create_backdoor", "Create Backdoor Users", "Create global backdoor users"),
    PermissionSeed("tenants.read", "Read Tenants", "View tenants"),
    PermissionSeed("tenants.create", "Create Tenants", "Create tenants"),
    PermissionSeed("tenants.update", "Update Tenants", "Update tenants"),
    PermissionSeed("tenants.delete", "Delete Tenants", "Delete tenants"),
    PermissionSeed("channels.read", "Read Channels", "View channels"),
    PermissionSeed("channels.create", "Create Channels", "Create channels"),
    PermissionSeed("channels.update", "Update Channels", "Update channels"),
    PermissionSeed("channels.delete", "Delete Channels", "Delete channels"),
    PermissionSeed("channel_config.read", "Read Channel Config", "View channel configuration"),
    PermissionSeed("channel_config.update", "Update Channel Config", "Update channel configuration"),
    PermissionSeed("bot_actions.read", "Read Bot Actions", "View tenant bot actions"),
    PermissionSeed("bot_actions.create", "Create Bot Actions", "Create tenant bot actions"),
    PermissionSeed("bot_actions.update", "Update Bot Actions", "Update tenant bot actions"),
    PermissionSeed("bot_actions.delete", "Delete Bot Actions", "Delete tenant bot actions"),
    PermissionSeed("roles.read", "Read Roles", "View roles"),
    PermissionSeed("roles.create", "Create Roles", "Create roles"),
    PermissionSeed("roles.update", "Update Roles", "Update roles"),
    PermissionSeed("roles.delete", "Delete Roles", "Delete roles"),
    PermissionSeed("permissions.read", "Read Permissions", "View permission catalog"),
    PermissionSeed("messages.read", "Read Messages", "View conversation messages"),
    PermissionSeed("messages.send", "Send Messages", "Send outbound messages"),
    PermissionSeed("conversations.read", "Read Conversations", "View conversations"),
    PermissionSeed("conversations.update", "Update Conversations", "Update conversation state"),
    PermissionSeed("api_keys.manage", "Manage API Keys", "Create and revoke integration API keys"),
    PermissionSeed("ai.test", "Test AI", "Execute AI test endpoint"),
    PermissionSeed("realtime.read", "Read Realtime", "Consume realtime stream"),
)

BACKDOOR_ROLE_NAME = "BACKDOOR"
ADMIN_ROLE_NAME = "ADMIN"
TENANT_USER_ROLE_NAME = "TENANT_USER"

ROLE_DEFINITIONS: dict[str, str] = {
    BACKDOOR_ROLE_NAME: "Global role with full access to every permission",
    ADMIN_ROLE_NAME: "Tenant-level administration role",
    TENANT_USER_ROLE_NAME: "Tenant-level operational role",
}

ADMIN_PERMISSION_CODES: set[str] = {
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
    "users.create_admin",
    "tenants.read",
    "tenants.update",
    "channels.read",
    "channels.create",
    "channels.update",
    "channels.delete",
    "channel_config.read",
    "channel_config.update",
    "bot_actions.read",
    "bot_actions.create",
    "bot_actions.update",
    "bot_actions.delete",
    "roles.read",
    "roles.create",
    "roles.update",
    "roles.delete",
    "permissions.read",
    "messages.read",
    "messages.send",
    "conversations.read",
    "conversations.update",
    "api_keys.manage",
    "ai.test",
    "realtime.read",
}

TENANT_USER_PERMISSION_CODES: set[str] = {
    "channels.read",
    "channel_config.read",
    "bot_actions.read",
    "messages.read",
    "messages.send",
    "conversations.read",
    "conversations.update",
    "realtime.read",
}
