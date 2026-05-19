import { Bot, User, X } from 'lucide-react';
import MultiSelect from '@/components/ui/MultiSelect';
import type { UserTypeDefinition } from '@/types/chat';

interface Props {
  search: string;
  onSearchChange: (value: string) => void;
  selectedMode: 'all' | 'ai' | 'human';
  onModeChange: (value: 'all' | 'ai' | 'human') => void;
  selectedUserTypes: string[];
  onUserTypesChange: (value: string[]) => void;
  userTypeOptions: UserTypeDefinition[];
  userTypeMap: Record<string, UserTypeDefinition>;
  onClearFilters: () => void;
}

export default function ConversationsFilters({
  search,
  onSearchChange,
  selectedMode,
  onModeChange,
  selectedUserTypes,
  onUserTypesChange,
  userTypeOptions,
  userTypeMap,
  onClearFilters,
}: Props) {
  const hasActiveFilters = !!search.trim() || selectedMode !== 'all' || selectedUserTypes.length > 0;

  return (
    <div className="flex-shrink-0 space-y-2.5 border-b border-slate-100 p-3">
      <div className="rounded-xl border border-slate-200 bg-white p-1">
        <div className="grid grid-cols-3 gap-1">
          {[
            { key: 'all', label: 'Todos', icon: null },
            { key: 'ai', label: 'AI', icon: <Bot className="h-3.5 w-3.5" /> },
            { key: 'human', label: 'Humano', icon: <User className="h-3.5 w-3.5" /> },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onModeChange(item.key as 'all' | 'ai' | 'human')}
              className={`inline-flex h-8 items-center justify-center gap-1.5 rounded-lg px-2 text-xs font-semibold transition ${
                selectedMode === item.key
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <MultiSelect
        label={undefined}
        options={userTypeOptions.map((item) => ({
          value: item.key,
          label: item.label,
          icon: (
            <span
              aria-hidden
              className="h-2.5 w-2.5 rounded-full ring-2 ring-white shadow-sm"
              style={{ backgroundColor: item.color }}
            />
          ),
        }))}
        value={selectedUserTypes}
        onChange={onUserTypesChange}
        placeholder="Filtrar por tipo de usuario"
      />

      <div className="flex flex-wrap gap-1.5">
        {selectedUserTypes.map((typeKey) => {
          const type = userTypeMap[typeKey];
          if (!type) return null;
          return (
            <span
              key={typeKey}
              className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset"
              style={{ backgroundColor: `${type.color}20`, color: type.color, borderColor: `${type.color}55` }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: type.color }} />
              {type.label}
            </span>
          );
        })}
      </div>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className="inline-flex items-center gap-1 text-xs font-medium text-sky-700 transition-colors hover:text-sky-800"
        >
          <X className="h-3 w-3" />
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
