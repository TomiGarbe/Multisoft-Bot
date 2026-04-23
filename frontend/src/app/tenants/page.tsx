'use client';

import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import { ToastViewport, useToast } from '@/components/ui/toast';
import TenantsTable from '@/components/tenants/TenantsTable';
import TenantForm from '@/components/tenants/TenantForm';
import { useTenantsPage } from '@/hooks/tenants/useTenantsPage';

export default function TenantsPage() {
  const toast = useToast();

  const {
    hasToken,
    tenants,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedTenant,
    openCreate,
    openEdit,
    handleDelete,
    setIsFormOpen,
    loadTenants,
  } = useTenantsPage(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Tenants</h1>
          <Button onClick={openCreate}>+ Create Tenant</Button>
        </div>

        {error && <div className="text-red-500">{error}</div>}

        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <TenantsTable
            tenants={tenants}
            isDeletingId={isDeletingId}
            onEdit={openEdit}
            onDelete={handleDelete}
          />
        )}
      </div>

      <TenantForm
        isOpen={isFormOpen}
        tenant={selectedTenant}
        onClose={() => setIsFormOpen(false)}
        onSaved={(msg) => {
          toast.success(msg);
          void loadTenants();
        }}
      />
    </AppLayout>
  );
}