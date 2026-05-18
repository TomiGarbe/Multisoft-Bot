interface SettingsTabsProps {
  tabs: Array<{ key: string; label: string; icon?: React.ReactNode }>;
  activeTab: string;
  onChange: (tab: string) => void;
}

export default function SettingsTabs({ tabs, activeTab, onChange }: SettingsTabsProps) {
  return (
    <div className="scrollbar-thin overflow-x-auto">
      <div className="inline-flex min-w-full gap-1 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
        {tabs.map((tab) => {
          const active = tab.key === activeTab;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onChange(tab.key)}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-150 ${
                active
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              {tab.icon ? (
                <span className={`inline-flex [&_svg]:h-4 [&_svg]:w-4 ${active ? 'opacity-100' : 'opacity-70'}`}>
                  {tab.icon}
                </span>
              ) : null}
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
