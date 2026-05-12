import { Link2 } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import IntegrationForm from '@/components/integrations/IntegrationForm';
import IntegrationsTable from '@/components/integrations/IntegrationsTable';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { useIntegrations } from '@/hooks/useIntegrations';

export default function IntegracionesPage() {
  const toast = useToast();
  const {
    hasToken,
    loading,
    error,
    items,
    isFormOpen,
    loadingDetail,
    selectedItem,
    submitting,
    workingId,
    testResult,
    canRead,
    canCreate,
    canUpdate,
    canDelete,
    setIsFormOpen,
    openCreate,
    openEdit,
    save,
    toggleEnabled,
    remove,
    runTest,
  } = useIntegrations(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Integraciones"
          description="Gestiona integraciones HTTP por tenant con auth, headers, body y pruebas seguras via backend."
          actions={
            <Button onClick={openCreate} disabled={!canCreate}>
              <Link2 className="mr-2 h-4 w-4" /> Nueva integracion
            </Button>
          }
        />

        {!canRead ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            No tienes permiso bot_actions.read para ver integraciones.
          </div>
        ) : null}

        {error ? <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}

        {canRead && (loading ? (
          <div className="text-center text-sm text-slate-500">Cargando integraciones...</div>
        ) : (
          <IntegrationsTable
            items={items}
            workingId={workingId}
            canUpdate={canUpdate}
            canDelete={canDelete}
            onEdit={openEdit}
            onToggle={toggleEnabled}
            onTest={openEdit}
            onDelete={remove}
          />
        ))}
      </div>

      <IntegrationForm
        open={isFormOpen}
        loadingDetail={loadingDetail}
        integration={selectedItem}
        submitting={submitting}
        canUpdate={canUpdate || canCreate}
        onClose={() => setIsFormOpen(false)}
        onSave={save}
        onTest={(variables) => runTest(selectedItem?.id ?? '', variables)}
        testResult={testResult}
      />
    </AppLayout>
  );
}
