export interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string | null;
}

export interface Role {
  id: string;
  name: string;
  description?: string | null;
  permissions: Permission[];
}

export interface CreateRoleInput {
  name: string;
  description?: string | null;
  permissions: string[];
}

export interface UpdateRoleInput {
  name?: string;
  description?: string | null;
  permissions?: string[];
}

export interface UserRoleSummary {
  id: string;
  name: string;
  description?: string | null;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role?: UserRoleSummary | null;
  permissions: Permission[];
  is_active?: boolean;
  is_backdoor?: boolean;
}

export interface CreateUserInput {
  name: string;
  email: string;
  password: string;
  role_id?: string | null;
  permissions?: string[];
  is_active?: boolean;
  is_backdoor?: boolean;
}

export interface UpdateUserInput {
  name?: string;
  email?: string;
  password?: string;
  role_id?: string | null;
  permissions?: string[];
  is_active?: boolean;
  is_backdoor?: boolean;
}
