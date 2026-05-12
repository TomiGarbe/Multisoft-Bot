export type IntegrationHttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
export type IntegrationAuthType = 'none' | 'bearer' | 'api_key' | 'basic' | 'custom';
export type IntegrationApiKeyLocation = 'header' | 'query';

export interface IntegrationListItem {
  id: string;
  name: string;
  description?: string | null;
  enabled: boolean;
  method: IntegrationHttpMethod;
  url: string;
  updated_at: string;
}

export interface IntegrationVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
  required: boolean;
  description?: string | null;
}

export interface IntegrationResponseConfig {
  response_type: 'json' | 'text';
  success_path?: string | null;
  error_path?: string | null;
}

export type IntegrationAuthConfig =
  | { type: 'none' }
  | { type: 'bearer'; token: string }
  | { type: 'api_key'; key: string; value: string; location: IntegrationApiKeyLocation }
  | { type: 'basic'; username: string; password: string }
  | { type: 'custom'; headers: Record<string, string> };

export interface IntegrationItem extends IntegrationListItem {
  trigger_prompt?: string | null;
  ai_instructions?: string | null;
  headers_jsonb?: Record<string, string> | null;
  query_params_jsonb?: Record<string, string> | null;
  body_jsonb?: unknown;
  variables_jsonb: IntegrationVariable[];
  auth_jsonb: IntegrationAuthConfig;
  response_config_jsonb: IntegrationResponseConfig;
  timeout_ms?: number | null;
  retry_count?: number | null;
  created_at: string;
}

export interface IntegrationPayload {
  name: string;
  description?: string | null;
  enabled: boolean;
  trigger_prompt?: string | null;
  ai_instructions?: string | null;
  method: IntegrationHttpMethod;
  url: string;
  headers_jsonb?: Record<string, string> | null;
  query_params_jsonb?: Record<string, string> | null;
  body_jsonb?: unknown;
  variables_jsonb: IntegrationVariable[];
  auth_jsonb: IntegrationAuthConfig;
  response_config_jsonb: IntegrationResponseConfig;
  timeout_ms?: number | null;
  retry_count?: number | null;
}

export interface IntegrationTestResponse {
  request: Record<string, unknown>;
  response: {
    success: boolean;
    status_code?: number | null;
    headers: Record<string, string>;
    data?: unknown;
    text?: string | null;
    duration_ms: number;
    error?: string | null;
  };
  timing: { duration_ms: number };
  success: boolean;
  error?: string | null;
}
