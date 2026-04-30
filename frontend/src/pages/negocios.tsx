import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import TenantsForm from '@/components/tenants/TenantsForm';
import TenantsTable from '@/components/tenants/TenantsTable';
import { useNegocios } from '@/hooks/useNegocios';

export default function TenantsPage() {
  const toast = useToast();
  const {
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

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Negocios"
          description="Administra los negocios registrados en la plataforma."
          actions={<Button onClick={createNegocio}>+ Crear negocio</Button>}
        />

        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        {loading ? (
          <div className="text-center text-sm text-slate-500">Cargando negocios...</div>
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
