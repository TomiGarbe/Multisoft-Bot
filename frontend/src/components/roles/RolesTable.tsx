import { Pencil, Trash2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import IconButton from '@/components/ui/IconButton';
import Table from '@/components/ui/Table';
import type { Role } from '@/types/access';

interface Props {
  roles: Role[];
  isDeletingId: string | null;
  onEdit: (role: Role) => void;
  onDelete: (role: Role) => void;
}

export default function RolesTable({ roles, isDeletingId, onEdit, onDelete }: Props) {
  return (
    <Table
      headers={['Nombre', 'Descripcion', 'Permisos', '']}
      hasRows={roles.length > 0}
      emptyMessage="No se encontraron roles."
    >
      {roles.map((role) => (
        <tr key={role.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{role.name}</td>
          <td className="px-4 py-3 text-sm text-slate-600">{role.description ?? '-'}</td>
          <td className="px-4 py-3 text-sm">
            <Badge tone="info" label={`${role.permissions?.length ?? 0} permisos`} variant="soft" />
          </td>
          <td className="px-4 py-3 text-sm">
            <div className="flex items-center justify-end gap-1.5">
              <IconButton
                icon={<Pencil />}
                label="Editar"
                size="sm"
                variant="ghost"
                onClick={() => onEdit(role)}
              />
              <IconButton
                icon={<Trash2 />}
                label="Eliminar"
                size="sm"
                variant="danger"
                onClick={() => onDelete(role)}
                disabled={isDeletingId === role.id}
              />
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
