import api from '@/services/api';
import type { CreateRoleInput, Role, UpdateRoleInput } from '@/types/access';

export async function getRoles(): Promise<Role[]> {
  const { data } = await api.get<Role[]>('/roles');
  return data;
}

export async function createRole(payload: CreateRoleInput): Promise<Role> {
  const { data } = await api.post<Role>('/roles', payload);
  return data;
}

export async function updateRole(roleId: string, payload: UpdateRoleInput): Promise<Role> {
  const { data } = await api.put<Role>(`/roles/${roleId}`, payload);
  return data;
}

export async function deleteRole(roleId: string): Promise<void> {
  await api.delete(`/roles/${roleId}`);
}
