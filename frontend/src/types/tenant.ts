export interface Tenant {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
  industry?: string | null;
  timezone?: string | null;
}

export interface TenantCreate {
  name: string;
  slug: string;
  description?: string;
  industry?: string;
  timezone?: string;
}

export interface TenantUpdate {
  name?: string;
  slug?: string;
  description?: string;
  is_active?: boolean;
  industry?: string;
  timezone?: string;
}