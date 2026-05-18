import { Pencil, Trash2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import IconButton from '@/components/ui/IconButton';
import Table from '@/components/ui/Table';
import { TENANT_TIMEZONE_LABEL_BY_VALUE } from '@/constants/timezones';
import type { Tenant } from '@/types/tenant';

interface Props {
  tenants: Tenant[];
  isDeletingId: string | null;
  onEdit: (tenant: Tenant) => void;
  onDelete: (tenant: Tenant) => void;
}

export default function TenantsTable({ tenants, isDeletingId, onEdit, onDelete }: Props) {
  return (
    <Table
      headers={['Nombre', 'Slug', 'Industria', 'Zona horaria', 'Descripcion', 'Estado', '']}
      hasRows={tenants.length > 0}
      emptyMessage="No se encontraron negocios."
    >
      {tenants.map((tenant) => (
        <tr key={tenant.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{tenant.name}</td>
          <td className="px-4 py-3 text-sm text-slate-600">
            <code className="rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-700">
              {tenant.slug}
            </code>
          </td>
          <td className="px-4 py-3 text-sm text-slate-600">{tenant.industry ?? '-'}</td>
          <td className="px-4 py-3 text-sm text-slate-600">
            {(tenant.timezone && TENANT_TIMEZONE_LABEL_BY_VALUE[tenant.timezone]) || tenant.timezone || '-'}
          </td>
          <td className="max-w-[320px] px-4 py-3 text-sm text-slate-600">
            <p className="line-clamp-2">{tenant.description ?? '-'}</p>
          </td>
          <td className="px-4 py-3">
            <Badge
              tone={tenant.is_active ? 'success' : 'neutral'}
              label={tenant.is_active ? 'Activo' : 'Inactivo'}
              variant="dot"
            />
          </td>
          <td className="px-4 py-3">
            <div className="flex items-center justify-end gap-1.5">
              <IconButton
                icon={<Pencil />}
                label="Editar"
                size="sm"
                variant="ghost"
                onClick={() => onEdit(tenant)}
              />
              <IconButton
                icon={<Trash2 />}
                label="Eliminar"
                size="sm"
                variant="danger"
                onClick={() => onDelete(tenant)}
                disabled={isDeletingId === tenant.id}
              />
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
