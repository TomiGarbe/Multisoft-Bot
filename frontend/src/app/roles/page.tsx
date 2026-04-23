'use client';

import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import { ToastViewport, useToast } from '@/components/ui/toast';
import RoleForm from '@/components/roles/RoleForm';
import RolesTable from '@/components/roles/RolesTable';
import { useRolesPage } from '@/hooks/roles/useRolesPage';

export default function RolesPage() {
  const toast = useToast();

  const {
    hasToken,
    roles,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedRole,
    openCreate,
    openEdit,
    handleDelete,
    setIsFormOpen,
    loadRoles,
  } = useRolesPage(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <section className="flex flex-col items-start justify-between gap-4 rounded-2xl border bg-white p-6 shadow-sm md:flex-row md:items-center">
          <div>
            <h1 className="text-3xl font-bold">Roles</h1>
            <p className="mt-2 text-sm text-slate-600">
              Manage system roles and permissions.
            </p>
          </div>

          <Button onClick={openCreate}>+ Create Role</Button>
        </section>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="text-center text-sm text-slate-500">
            Loading roles...
          </div>
        ) : (
          <RolesTable
            roles={roles}
            isDeletingId={isDeletingId}
            onEdit={openEdit}
            onDelete={handleDelete}
          />
        )}
      </div>

      <RoleForm
        open={isFormOpen}
        role={selectedRole}
        onClose={() => setIsFormOpen(false)}
        onSuccess={(message) => {
          toast.success(message);
          void loadRoles();
        }}
      />
    </AppLayout>
  );
}