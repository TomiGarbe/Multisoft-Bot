import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import ChannelsForm from '@/components/channels/ChannelsForm';
import ChannelsTable from '@/components/channels/ChannelsTable';
import { useConfig } from '@/hooks/useConfig';

export default function CanalesPage() {
  const toast = useToast();
  const {
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

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Canales"
          description="Administra canales y su configuración operativa."
          actions={<Button onClick={createConfig}>+ Crear canal</Button>}
        />
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {loading ? (
          <div className="text-center text-sm text-slate-500">Cargando canales...</div>
        ) : (
          <ChannelsTable channels={configItems} isDeletingId={deletingId} onEdit={updateConfig} onDelete={deleteConfig} />
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
