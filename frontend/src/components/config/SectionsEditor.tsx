import SectionForm from '@/components/config/SectionForm';
import type { BotConfig, BotConfigSection } from '@/hooks/useBotConfig';

interface SectionsEditorProps {
  config: BotConfig;
  onSaveSection: (section: string, data: BotConfigSection) => Promise<void>;
}

export default function SectionsEditor({ config, onSaveSection }: SectionsEditorProps) {
  return (
    <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {Object.entries(config).map(([sectionKey, sectionValue]) => (
        <SectionForm
          key={sectionKey}
          sectionKey={sectionKey}
          value={sectionValue}
          onSave={(nextValue) => onSaveSection(sectionKey, nextValue)}
        />
      ))}
    </section>
  );
}
