import { Plus, ShieldCheck } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import RolesForm from '@/components/roles/RolesForm';
import RolesTable from '@/components/roles/RolesTable';
import { useRoles } from '@/hooks/useRoles';

export default function RolesPage() {
  const toast = useToast();
  const {
    authResolved,
    hasToken,
    roles,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedRole,
    createRole,
    updateRole,
    deleteRole,
    setIsFormOpen,
    fetchRoles,
  } = useRoles(toast);

  if (!authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<ShieldCheck className="h-6 w-6" />}
          title="Roles"
          description="Administra roles y permisos de este negocio."
          actions={
            <Button leadingIcon={<Plus />} onClick={createRole}>
              Crear rol
            </Button>
          }
        />
        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}
        {loading ? (
          <EmptyState title="Cargando roles..." description="Obteniendo la lista." compact />
        ) : (
          <RolesTable
            roles={roles}
            isDeletingId={deletingId}
            onEdit={updateRole}
            onDelete={deleteRole}
          />
        )}
      </div>
      <RolesForm
        open={isFormOpen}
        role={selectedRole}
        onClose={() => setIsFormOpen(false)}
        onSuccess={(message) => {
          toast.success(message);
          void fetchRoles();
        }}
      />
    </AppLayout>
  );
}
