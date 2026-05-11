import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
import { KeyRound, Pencil, Power, Trash } from 'lucide-react';
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
      headers={['Nombre', 'Email', 'Rol', 'Estado', 'Ultimo acceso', 'Fecha creacion', 'Acciones']}
      hasRows={users.length > 0}
      emptyMessage="No hay usuarios creados todavia."
    >
      {users.map((user) => {
        const isActive = statusLabel(user) === 'Activo';
        const isBusy = isDeletingId === user.id || isUpdatingId === user.id;

        return (
          <tr key={user.id}>
            <td className="px-4 py-3 text-sm font-medium text-slate-900">{user.name}</td>
            <td className="px-4 py-3 text-sm text-slate-700">{user.email}</td>
            <td className="px-4 py-3 text-sm text-slate-700">
              <span className="inline-flex rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
                {resolveRoleLabel(user)}
              </span>
            </td>
            <td className="px-4 py-3">
              <span
                className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                  isActive ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
                }`}
              >
                {statusLabel(user)}
              </span>
            </td>
            <td className="px-4 py-3 text-sm text-slate-700">{formatDate(user.last_login_at ?? user.last_access_at)}</td>
            <td className="px-4 py-3 text-sm text-slate-700">{formatDate(user.created_at)}</td>
            <td className="px-4 py-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <Button variant="secondary" className="p-2" onClick={() => onEdit(user)} title="Editar" aria-label="Editar">
                  <Pencil size={16} />
                </Button>
                <Button
                  variant="secondary"
                  className="p-2"
                  onClick={() => onToggleStatus(user)}
                  disabled={isBusy}
                  title={isActive ? 'Desactivar' : 'Activar'}
                  aria-label={isActive ? 'Desactivar' : 'Activar'}
                >
                  <Power size={16} />
                </Button>
                <Button
                  variant="secondary"
                  className="p-2"
                  onClick={() => onResetPassword(user)}
                  disabled={isBusy}
                  title="Resetear contrasena"
                  aria-label="Resetear contrasena"
                >
                  <KeyRound size={16} />
                </Button>
                <Button
                  variant="danger"
                  className="p-2"
                  onClick={() => onDelete(user)}
                  disabled={isBusy}
                  title="Eliminar"
                  aria-label="Eliminar"
                >
                  <Trash size={16} />
                </Button>
              </div>
            </td>
          </tr>
        );
      })}
    </Table>
  );
}
