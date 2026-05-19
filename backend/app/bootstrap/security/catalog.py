from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class PermissionUiMetadata:
    module: str
    pages: tuple[str, ...]
    assignable: bool = True
    internal_only: bool = False
    backdoor_only: bool = False
    tenant_visible: bool = True


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
    PermissionSeed("contacts.read", "Read Contacts", "View contacts"),
    PermissionSeed("contacts.update", "Update Contacts", "Update contact data"),
    PermissionSeed("contact_notes.read", "Read Contact Notes", "View contact notes"),
    PermissionSeed("contact_notes.update", "Update Contact Notes", "Create and update contact notes"),
    PermissionSeed("contact_tags.read", "Read Contact Tags", "View contact tags"),
    PermissionSeed("contact_tags.update", "Update Contact Tags", "Create and update contact tags"),
    PermissionSeed("contact_types.read", "Read Contact Types", "View contact type catalog"),
    PermissionSeed("contact_types.update", "Update Contact Types", "Update contact types"),
    PermissionSeed("user_types.read", "Read User Types", "View user types"),
    PermissionSeed("user_types.update", "Update User Types", "Update user types"),
    PermissionSeed("api_keys.manage", "Manage API Keys", "Create and revoke integration API keys"),
    PermissionSeed("ai.test", "Test AI", "Execute AI test endpoint"),
    PermissionSeed("analytics.read", "Read Analytics", "View tenant/global aggregated analytics"),
    PermissionSeed("realtime.read", "Read Realtime", "Consume realtime stream"),
)

PERMISSION_UI_METADATA: dict[str, PermissionUiMetadata] = {
    "analytics.read": PermissionUiMetadata(module="analytics", pages=("dashboard",)),
    "conversations.read": PermissionUiMetadata(module="conversations", pages=("conversations",)),
    "conversations.update": PermissionUiMetadata(module="conversations", pages=("conversations",)),
    "messages.read": PermissionUiMetadata(module="messages", pages=("conversations",)),
    "messages.send": PermissionUiMetadata(module="messages", pages=("conversations",)),
    "users.read": PermissionUiMetadata(module="users", pages=("users",)),
    "users.create": PermissionUiMetadata(module="users", pages=("users",)),
    "users.update": PermissionUiMetadata(module="users", pages=("users",)),
    "users.delete": PermissionUiMetadata(module="users", pages=("users",)),
    "users.create_admin": PermissionUiMetadata(
        module="users", pages=(), assignable=False, internal_only=True, tenant_visible=False
    ),
    "users.create_backdoor": PermissionUiMetadata(
        module="users", pages=(), assignable=False, internal_only=True, backdoor_only=True, tenant_visible=False
    ),
    "roles.read": PermissionUiMetadata(module="roles", pages=("roles", "users")),
    "roles.create": PermissionUiMetadata(module="roles", pages=("roles",)),
    "roles.update": PermissionUiMetadata(module="roles", pages=("roles",)),
    "roles.delete": PermissionUiMetadata(module="roles", pages=("roles",)),
    "permissions.read": PermissionUiMetadata(module="permissions", pages=("roles", "users")),
    "channels.read": PermissionUiMetadata(module="channels", pages=("channels", "conversations")),
    "channels.create": PermissionUiMetadata(module="channels", pages=("channels",)),
    "channels.update": PermissionUiMetadata(module="channels", pages=("channels",)),
    "channels.delete": PermissionUiMetadata(module="channels", pages=("channels",)),
    "channel_config.read": PermissionUiMetadata(module="channel_config", pages=("channels", "settings", "integrations")),
    "channel_config.update": PermissionUiMetadata(module="channel_config", pages=("channels", "settings", "integrations")),
    "bot_actions.read": PermissionUiMetadata(module="bot_actions", pages=("integrations", "settings")),
    "bot_actions.create": PermissionUiMetadata(module="bot_actions", pages=("integrations",)),
    "bot_actions.update": PermissionUiMetadata(module="bot_actions", pages=("integrations",)),
    "bot_actions.delete": PermissionUiMetadata(module="bot_actions", pages=("integrations",)),
    "api_keys.manage": PermissionUiMetadata(module="api_keys", pages=("settings",)),
    "contacts.read": PermissionUiMetadata(module="contacts", pages=("conversations",)),
    "contacts.update": PermissionUiMetadata(module="contacts", pages=("conversations",)),
    "contact_notes.read": PermissionUiMetadata(module="contact_notes", pages=("conversations",)),
    "contact_notes.update": PermissionUiMetadata(module="contact_notes", pages=("conversations",)),
    "contact_tags.read": PermissionUiMetadata(module="contact_tags", pages=("conversations", "settings")),
    "contact_tags.update": PermissionUiMetadata(module="contact_tags", pages=("conversations", "settings")),
    "contact_types.read": PermissionUiMetadata(module="contact_types", pages=("conversations", "settings")),
    "contact_types.update": PermissionUiMetadata(module="contact_types", pages=("conversations", "settings")),
    "user_types.read": PermissionUiMetadata(module="user_types", pages=("conversations", "settings")),
    "user_types.update": PermissionUiMetadata(module="user_types", pages=("conversations", "settings")),
    "tenants.read": PermissionUiMetadata(module="tenants", pages=(), assignable=False, internal_only=True, backdoor_only=True, tenant_visible=False),
    "tenants.create": PermissionUiMetadata(module="tenants", pages=(), assignable=False, internal_only=True, backdoor_only=True, tenant_visible=False),
    "tenants.update": PermissionUiMetadata(module="tenants", pages=(), assignable=False, internal_only=True, backdoor_only=True, tenant_visible=False),
    "tenants.delete": PermissionUiMetadata(module="tenants", pages=(), assignable=False, internal_only=True, backdoor_only=True, tenant_visible=False),
    "ai.test": PermissionUiMetadata(module="ai", pages=(), assignable=False, internal_only=True, tenant_visible=False),
    "realtime.read": PermissionUiMetadata(module="realtime", pages=(), assignable=False, internal_only=True, tenant_visible=False),
}

BACKDOOR_ROLE_NAME = "Backdoor"
ADMIN_ROLE_NAME = "Administrador"

ROLE_DEFINITIONS: dict[str, str] = {
    BACKDOOR_ROLE_NAME: "Global role with full access to every permission",
    ADMIN_ROLE_NAME: "Tenant-level administration role",
}

ADMIN_PERMISSION_CODES: set[str] = {
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
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
    "analytics.read",
    "realtime.read",
}
