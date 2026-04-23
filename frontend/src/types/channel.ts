export interface Channel {
  id: string;
  tenant_id: string;
  type: string;
  name: string;
  external_id: string;
  config?: Record<string, any>;
  is_active: boolean;
}

export interface ChannelCreate {
  tenant_id: string;
  type: string;
  name: string;
  external_id: string;
  config?: Record<string, any>;
  is_active: boolean;
}

export interface ChannelUpdate {
  type?: string;
  name?: string;
  external_id?: string;
  config?: Record<string, any>;
  is_active?: boolean;
}
