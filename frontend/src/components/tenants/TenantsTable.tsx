import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
import { Pencil, Trash } from 'lucide-react';
import type { Tenant } from '@/types/tenant';

interface Props {
  tenants: Tenant[];
  isDeletingId: string | null;
  onEdit: (tenant: Tenant) => void;
  onDelete: (tenant: Tenant) => void;
}

export default function TenantsTable({
  tenants,
  isDeletingId,
  onEdit,
  onDelete,
}: Props) {
  return (
    <Table
      headers={['Nombre', 'Slug', 'Industria', 'Zona horaria', 'Descripción', 'Estado', 'Acciones']}
      hasRows={tenants.length > 0}
      emptyMessage="No se encontraron negocios."
    >
      {tenants.map((tenant) => (
        <tr key={tenant.id}>
          <td className="px-4 py-3 font-medium">{tenant.name}</td>
          <td className="px-4 py-3 text-sm text-slate-600">{tenant.slug}</td>
          <td className="px-4 py-3 text-sm text-slate-600">{tenant.industry ?? '�'}</td>
          <td className="px-4 py-3 text-sm text-slate-600">{tenant.timezone ?? '�'}</td>
          <td className="px-4 py-3 text-sm text-slate-600">{tenant.description ?? '�'}</td>

          <td className="px-4 py-3">
            <span
              className={`px-2 py-1 text-xs rounded-full ${
                tenant.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
              }`}
            >
              {tenant.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </td>

          <td className="px-4 py-3">
            <div className="flex gap-2">
              <Button
                variant="secondary"
                className="p-2"
                onClick={() => onEdit(tenant)}
                title="Editar"
                aria-label="Editar"
              >
                <Pencil size={16} />
              </Button>

              <Button
                variant="danger"
                className="p-2"
                onClick={() => onDelete(tenant)}
                disabled={isDeletingId === tenant.id}
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
