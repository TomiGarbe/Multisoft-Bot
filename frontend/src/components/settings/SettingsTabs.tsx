interface SettingsTabsProps {
  tabs: Array<{ key: string; label: string }>;
  activeTab: string;
  onChange: (tab: string) => void;
}

export default function SettingsTabs({ tabs, activeTab, onChange }: SettingsTabsProps) {
  return (
    <div className="overflow-x-auto">
      <div className="inline-flex min-w-full gap-2 rounded-xl border border-slate-200 bg-white p-2">
        {tabs.map((tab) => {
          const active = tab.key === activeTab;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onChange(tab.key)}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                active ? 'bg-sky-600 text-white' : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
