export type UserTypeItem = { key: string; label: string; color: string; is_default: boolean };

export type UserTypesEditable = {
  default_type: string;
  types: UserTypeItem[];
};

export type TenantSettingsEditable = {
  name: string;
  timezone: string;
  industry: string;
};

export type ChannelSettingsEditable = {
  max_bot_messages: number;
  max_bot_messages_message: string;
  human_handoff_reset_hours: number;
  unsupported_content_message: string;
};
