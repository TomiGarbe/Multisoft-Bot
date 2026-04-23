import api from '@/services/api';
import type { Permission } from '@/types/access';

export async function getPermissions(): Promise<Permission[]> {
  const { data } = await api.get<Permission[]>('/permissions');
  return data;
}
