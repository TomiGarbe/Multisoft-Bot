import api from '@/services/api';
import type { CreateUserInput, UpdateUserInput, User } from '@/types/access';

export async function getUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/users');
  return data;
}

export async function createUser(payload: CreateUserInput): Promise<User> {
  const { data } = await api.post<User>('/users', payload);
  return data;
}

export async function updateUser(userId: string, payload: UpdateUserInput): Promise<User> {
  const { data } = await api.put<User>(`/users/${userId}`, payload);
  return data;
}

export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`);
}
