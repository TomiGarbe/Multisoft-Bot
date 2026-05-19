import { Cable, Lock, Plus } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import IntegrationForm from '@/components/integrations/IntegrationForm';
import IntegrationsTable from '@/components/integrations/IntegrationsTable';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { useIntegrations } from '@/hooks/useIntegrations';

export default function IntegracionesPage() {
  const toast = useToast();
  const {
    authResolved,
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

  if (!authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<Cable className="h-6 w-6" />}
          title="Integraciones"
          description="Gestiona integraciones HTTP por tenant con auth, headers, body y pruebas seguras via backend."
          actions={
            <Button leadingIcon={<Plus />} onClick={openCreate} disabled={!canCreate}>
              Nueva integracion
            </Button>
          }
        />

        {!canRead ? (
          <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            <Lock className="mt-0.5 h-4 w-4 shrink-0" />
            <span>No tienes permiso bot_actions.read para ver integraciones.</span>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {canRead &&
          (loading ? (
            <EmptyState title="Cargando integraciones..." description="Obteniendo la lista." compact />
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
