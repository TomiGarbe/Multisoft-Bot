import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
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
      headers={['Name', 'Slug', 'Industry', 'Timezone', 'Status', 'Actions']}
      hasRows={tenants.length > 0}
      emptyMessage="No tenants found."
    >
      {tenants.map((tenant) => (
        <tr key={tenant.id}>
          <td className="px-4 py-3 font-medium">{tenant.name}</td>
          <td>{tenant.slug}</td>
          <td>{tenant.industry ?? '—'}</td>
          <td>{tenant.timezone ?? '—'}</td>
          <td className="px-4 py-3 text-sm text-slate-600">
            {tenant.description ?? '—'}
          </td>

          <td className="px-4 py-3">
            <span
              className={`px-2 py-1 text-xs rounded-full ${
                tenant.is_active
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {tenant.is_active ? 'Active' : 'Inactive'}
            </span>
          </td>

          <td className="px-4 py-3">
            <div className="flex gap-2">
              <Button onClick={() => onEdit(tenant)}>Edit</Button>

              <Button
                variant="danger"
                onClick={() => onDelete(tenant)}
                disabled={isDeletingId === tenant.id}
              >
                {isDeletingId === tenant.id ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}