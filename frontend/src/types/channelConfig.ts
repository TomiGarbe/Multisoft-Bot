export interface ChannelConfigValidationStatus {
  is_valid: boolean;
  missing_fields: string[];
}

export interface BotIdentityConfig {
  role: string;
  bot_name: string;
  industry: string;
  language: string;
  description: string;
}

export interface BotToneConfig {
  tone: string;
  style_rules: string[];
}

export interface BotRulesConfig {
  rules: string[];
  fallback_message: string;
}

export interface BotActionConfig {
  name: string;
  description: string;
}

export interface BotObjectiveConfig {
  description: string;
  cta_message: string;
  applies_to: string[];
  conversation_flow: string[];
}

export interface DataCollectionField {
  name: string;
  type: string;
}

export interface BotConfigEditable {
  identity: BotIdentityConfig;
  tone: BotToneConfig;
  rules: BotRulesConfig;
  actions: BotActionConfig[];
  objectives: BotObjectiveConfig[];
  data_collection: {
    fields: DataCollectionField[];
  };
}

export interface ChannelBotConfig {
  id: string;
  tenant_id: string;
  channel_id: string;
  is_active: boolean;
  version: number;
  config_jsonb: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
