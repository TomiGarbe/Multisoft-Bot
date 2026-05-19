import { Plus, Radio } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import ChannelsForm from '@/components/channels/ChannelsForm';
import ChannelsTable from '@/components/channels/ChannelsTable';
import { useConfig } from '@/hooks/useConfig';

export default function CanalesPage() {
  const toast = useToast();
  const {
    authResolved,
    hasToken,
    configItems,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedConfigItem,
    createConfig,
    updateConfig,
    deleteConfig,
    setIsFormOpen,
    fetchConfig,
  } = useConfig(toast);

  if (!authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<Radio className="h-6 w-6" />}
          title="Canales"
          description="Administra canales y su configuracion operativa."
          actions={
            <Button leadingIcon={<Plus />} onClick={createConfig}>
              Crear canal
            </Button>
          }
        />
        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}
        {loading ? (
          <EmptyState title="Cargando canales..." description="Obteniendo la lista." compact />
        ) : (
          <ChannelsTable
            channels={configItems}
            isDeletingId={deletingId}
            onEdit={updateConfig}
            onDelete={deleteConfig}
          />
        )}
      </div>
      <ChannelsForm
        isOpen={isFormOpen}
        channel={selectedConfigItem}
        onClose={() => setIsFormOpen(false)}
        onSaved={(message) => {
          toast.success(message);
          void fetchConfig();
        }}
      />
    </AppLayout>
  );
}
