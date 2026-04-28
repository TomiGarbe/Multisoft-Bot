import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import RolesForm from '@/components/roles/RolesForm';
import RolesTable from '@/components/roles/RolesTable';
import { useAdvisors } from '@/hooks/useAdvisors';

export default function AdvisorsPage() {
  const toast = useToast();
  const {
    hasToken,
    advisors,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedAdvisor,
    createAdvisor,
    updateAdvisor,
    deleteAdvisor,
    setIsFormOpen,
    fetchAdvisors,
  } = useAdvisors(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Advisors"
          description="Administra los advisors y sus permisos en la plataforma."
          actions={<Button onClick={createAdvisor}>+ Crear advisor</Button>}
        />

        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        {loading ? (
          <div className="text-center text-sm text-slate-500">Cargando advisors...</div>
        ) : (
          <RolesTable
            roles={advisors}
            isDeletingId={deletingId}
            onEdit={updateAdvisor}
            onDelete={deleteAdvisor}
          />
        )}
      </div>

      <RolesForm
        open={isFormOpen}
        role={selectedAdvisor}
        onClose={() => setIsFormOpen(false)}
        onSuccess={(message) => {
          toast.success(message);
          void fetchAdvisors();
        }}
      />
    </AppLayout>
  );
}
