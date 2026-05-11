import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
import { Pencil, Trash } from 'lucide-react';
import type { Role } from '@/types/access';

interface Props {
  roles: Role[];
  isDeletingId: string | null;
  onEdit: (role: Role) => void;
  onDelete: (role: Role) => void;
}

export default function RolesTable({
  roles,
  isDeletingId,
  onEdit,
  onDelete,
}: Props) {
  return (
    <Table
      headers={['Nombre', 'Descripcion', 'Acciones']}
      hasRows={roles.length > 0}
      emptyMessage="No se encontraron roles."
    >
      {roles.map((role) => (
        <tr key={role.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{role.name}</td>

          <td className="px-4 py-3 text-sm text-slate-700">{role.description ?? '-'}</td>

          <td className="px-4 py-3 text-sm">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                className="p-2"
                onClick={() => onEdit(role)}
                title="Editar"
                aria-label="Editar"
              >
                <Pencil size={16} />
              </Button>

              <Button
                variant="danger"
                className="p-2"
                onClick={() => onDelete(role)}
                disabled={isDeletingId === role.id}
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
