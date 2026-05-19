import { Building2, Plus } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import TenantsForm from '@/components/tenants/TenantsForm';
import TenantsTable from '@/components/tenants/TenantsTable';
import { useNegocios } from '@/hooks/useNegocios';

export default function TenantsPage() {
  const toast = useToast();
  const {
    authResolved,
    hasToken,
    negocios,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedNegocio,
    createNegocio,
    updateNegocio,
    deleteNegocio,
    setIsFormOpen,
    fetchNegocios,
  } = useNegocios(toast);

  if (!authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<Building2 className="h-6 w-6" />}
          title="Negocios"
          description="Administra los negocios registrados en la plataforma."
          actions={
            <Button leadingIcon={<Plus />} onClick={createNegocio}>
              Crear negocio
            </Button>
          }
        />

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <EmptyState title="Cargando negocios..." description="Obteniendo la lista." compact />
        ) : (
          <TenantsTable
            tenants={negocios}
            isDeletingId={deletingId}
            onEdit={updateNegocio}
            onDelete={deleteNegocio}
          />
        )}
      </div>

      <TenantsForm
        isOpen={isFormOpen}
        tenant={selectedNegocio}
        onClose={() => setIsFormOpen(false)}
        onSaved={(msg) => {
          toast.success(msg);
          void fetchNegocios();
        }}
      />
    </AppLayout>
  );
}
