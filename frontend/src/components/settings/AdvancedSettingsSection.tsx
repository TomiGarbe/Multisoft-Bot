import { Sparkles } from 'lucide-react';
import Card from '@/components/ui/Card';

export default function AdvancedSettingsSection() {
  return (
    <Card
      icon={<Sparkles className="h-5 w-5" />}
      title="Avanzado"
      description="Reservado para automatizaciones, analytics y configuracion avanzada futura."
    >
      <p className="text-sm text-slate-500">
        Proximamente: workflows, triggers personalizados y metricas avanzadas.
      </p>
    </Card>
  );
}
