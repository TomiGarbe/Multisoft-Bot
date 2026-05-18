import { KeyRound, Pencil, Power, Trash2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import IconButton from '@/components/ui/IconButton';
import Table from '@/components/ui/Table';
import type { User } from '@/types/access';

interface Props {
  users: User[];
  isDeletingId: string | null;
  isUpdatingId: string | null;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onToggleStatus: (user: User) => void;
  onResetPassword: (user: User) => void;
  statusLabel: (user: User) => string;
}

function formatDate(date?: string | null): string {
  if (!date) return '-';
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function resolveRoleLabel(user: User): string {
  const raw = (user.role?.name ?? '').trim();
  if (!raw) return 'Sin rol';
  const normalized = raw.toLowerCase();
  if (normalized.includes('admin')) return 'Administrador';
  if (normalized.includes('supervisor')) return 'Supervisor';
  if (normalized.includes('operator') || normalized.includes('operador')) return 'Operador';
  return raw;
}

function initialsOf(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

export default function UsersTable({
  users,
  isDeletingId,
  isUpdatingId,
  onEdit,
  onDelete,
  onToggleStatus,
  onResetPassword,
  statusLabel,
}: Props) {
  return (
    <Table
      headers={['Usuario', 'Rol', 'Estado', 'Ultimo acceso', 'Creacion', '']}
      hasRows={users.length > 0}
      emptyMessage="No hay usuarios creados todavia."
    >
      {users.map((user) => {
        const isActive = statusLabel(user) === 'Activo';
        const isBusy = isDeletingId === user.id || isUpdatingId === user.id;

        return (
          <tr key={user.id}>
            <td className="px-4 py-3 text-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700">
                  {initialsOf(user.name) || 'U'}
                </span>
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-900">{user.name}</p>
                  <p className="truncate text-xs text-slate-500">{user.email}</p>
                </div>
              </div>
            </td>
            <td className="px-4 py-3 text-sm">
              <Badge tone="info" label={resolveRoleLabel(user)} variant="soft" />
            </td>
            <td className="px-4 py-3">
              <Badge
                tone={isActive ? 'success' : 'neutral'}
                label={statusLabel(user)}
                variant="dot"
              />
            </td>
            <td className="px-4 py-3 text-sm text-slate-600">
              {formatDate(user.last_login_at ?? user.last_access_at)}
            </td>
            <td className="px-4 py-3 text-sm text-slate-600">{formatDate(user.created_at)}</td>
            <td className="px-4 py-3 text-sm">
              <div className="flex items-center justify-end gap-1.5">
                <IconButton
                  icon={<Pencil />}
                  label="Editar"
                  size="sm"
                  variant="ghost"
                  onClick={() => onEdit(user)}
                />
                <IconButton
                  icon={<Power />}
                  label={isActive ? 'Desactivar' : 'Activar'}
                  size="sm"
                  variant="ghost"
                  onClick={() => onToggleStatus(user)}
                  disabled={isBusy}
                />
                <IconButton
                  icon={<KeyRound />}
                  label="Resetear contrasena"
                  size="sm"
                  variant="ghost"
                  onClick={() => onResetPassword(user)}
                  disabled={isBusy}
                />
                <IconButton
                  icon={<Trash2 />}
                  label="Eliminar"
                  size="sm"
                  variant="danger"
                  onClick={() => onDelete(user)}
                  disabled={isBusy}
                />
              </div>
            </td>
          </tr>
        );
      })}
    </Table>
  );
}
