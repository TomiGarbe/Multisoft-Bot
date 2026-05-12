export interface ChannelConfigValidationStatus {
  is_valid: boolean;
  missing_fields: string[];
}

export type CustomFieldType = 'short_text' | 'long_text' | 'list' | 'group' | 'group_list';

export interface CustomFieldConfig {
  key: string;
  label: string;
  type: CustomFieldType;
  description: string;
  required: boolean;
  options: string[];
  fields: CustomFieldConfig[];
  item_fields: CustomFieldConfig[];
  notes: string[];
}

export interface ConfigSection {
  id: string;
  type: string;
  label: string;
  enabled: boolean;
  priority: number;
  fields?: Record<string, unknown>;
  entries?: Record<string, unknown>[];
  custom_fields?: CustomFieldConfig[];
  notes?: string;
}

export interface ConfigDocument {
  version: number;
  sections: ConfigSection[];
}

export type BotConfigEditable = ConfigDocument;

export interface ChannelBotConfig {
  id: string;
  tenant_id: string;
  channel_id: string;
  is_active: boolean;
  version: number;
  config_jsonb: ConfigDocument;
  created_at: string;
  updated_at: string;
}
