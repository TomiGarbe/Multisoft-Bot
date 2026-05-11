import Button from '@/components/ui/Button';
import type { Channel } from '@/types/channel';

interface IntegrationsSettingsSectionProps {
  channel: Channel | null;
}

export default function IntegrationsSettingsSection({ channel }: IntegrationsSettingsSectionProps) {
  if (!channel) {
    return (
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Provider no conectado. Conecta una integracion para habilitar configuracion especifica.
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
      <h2 className="text-lg font-semibold text-slate-900">Integraciones</h2>
      <p className="mt-1 text-sm text-slate-500">
        Configuracion por provider para <span className="font-medium text-slate-700">{channel.type}</span>.
      </p>

      <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
        <p className="text-sm text-slate-700">Esta integracion todava no tiene parametros especificos en frontend.</p>
        <p className="mt-1 text-sm text-slate-500">Proximo paso: agregar webhook, credenciales y estado de conexion por provider.</p>
        <div className="mt-3 flex gap-2">
          <Button variant="secondary">Configurar webhook</Button>
          <Button variant="secondary">Conectar provider</Button>
        </div>
      </div>
    </section>
  );
}
