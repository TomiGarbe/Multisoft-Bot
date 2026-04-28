import { useEffect } from 'react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import SectionsEditor from '@/components/config/SectionsEditor';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { useBotConfig } from '@/hooks/useBotConfig';
import { getToken } from '@/services/auth';

export default function ConfiguracionPage() {
  const router = useRouter();
  const toast = useToast();
  const hasToken = Boolean(getToken());
  const { config, loading, updateConfig } = useBotConfig();

  useEffect(() => {
    if (!hasToken) router.replace('/login');
  }, [hasToken, router]);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Configuración"
          description="Configura identidad, tono, reglas y objetivos del bot por secciones independientes."
        />

        {loading ? (
          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
            Cargando configuración...
          </div>
        ) : (
          <SectionsEditor
            config={config}
            onSaveSection={async (section, data) => {
              await updateConfig(section, data);
              toast.success(`Sección "${section}" actualizada.`);
            }}
          />
        )}
      </div>
    </AppLayout>
  );
}
