import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
import { Pencil, Trash } from 'lucide-react';
import type { User } from '@/types/access';

interface Props {
  users: User[];
  isDeletingId: string | null;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  statusLabel: (user: User) => string;
}

export default function UsersTable({
  users,
  isDeletingId,
  onEdit,
  onDelete,
  statusLabel,
}: Props) {
  return (
    <Table
      headers={['Nombre', 'Email', 'Rol', 'Negocio', 'Estado', 'Acciones']}
      hasRows={users.length > 0}
      emptyMessage="No se encontraron usuarios."
    >
      {users.map((user) => (
        <tr key={user.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{user.name}</td>

          <td className="px-4 py-3 text-sm text-slate-700">{user.email}</td>

          <td className="px-4 py-3 text-sm text-slate-700">
            <div className="flex items-center gap-2">
              <span>{user.role?.name ?? 'Sin rol'}</span>
              {user.is_backdoor && (
                <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">
                  Backdoor
                </span>
              )}
            </div>
          </td>

          <td className="px-4 py-3 text-sm text-slate-700">
            {user.is_backdoor ? (
              <span className="inline-flex rounded-full bg-violet-100 px-2.5 py-1 text-xs font-semibold text-violet-700">
                Backdoor
              </span>
            ) : user.tenant?.name ? (
              <span>{user.tenant.name}</span>
            ) : (
              <span className="text-slate-400">-</span>
            )}
          </td>

          <td className="px-4 py-3">
            <span
              className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                statusLabel(user) === 'Activo' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
              }`}
            >
              {statusLabel(user)}
            </span>
          </td>

          <td className="px-4 py-3 text-sm">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                className="p-2"
                onClick={() => onEdit(user)}
                title="Editar"
                aria-label="Editar"
              >
                <Pencil size={16} />
              </Button>

              <Button
                variant="danger"
                className="p-2"
                onClick={() => onDelete(user)}
                disabled={isDeletingId === user.id}
                title="Eliminar"
                aria-label="Eliminar"
              >
                <Trash size={16} />
              </Button>
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
