import api from '@/services/api';
import type { CreateUserInput, UpdateUserInput, User } from '@/types/access';

export async function getUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/users');
  return data;
}
export async function getGlobalUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/users/global');
  return data;
}

export async function createUser(payload: CreateUserInput): Promise<User> {
  const { data } = await api.post<User>('/users', payload);
  return data;
}
export async function createAdminUser(payload: CreateUserInput): Promise<User> {
  const { data } = await api.post<User>('/users/admin', payload);
  return data;
}
export async function createBackdoorUser(payload: CreateUserInput): Promise<User> {
  const { data } = await api.post<User>('/users/backdoor', payload);
  return data;
}
export async function getBusinessUsers(businessId: string): Promise<User[]> {
  const { data } = await api.get<User[]>(`/businesses/${businessId}/users`);
  return data;
}
export async function createBusinessUser(businessId: string, payload: CreateUserInput): Promise<User> {
  const { data } = await api.post<User>(`/businesses/${businessId}/users`, payload);
  return data;
}
export async function updateBusinessUser(businessId: string, userId: string, payload: UpdateUserInput): Promise<User> {
  const { data } = await api.put<User>(`/businesses/${businessId}/users/${userId}`, payload);
  return data;
}

export async function updateUser(userId: string, payload: UpdateUserInput): Promise<User> {
  const { data } = await api.put<User>(`/users/${userId}`, payload);
  return data;
}

export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`);
}
