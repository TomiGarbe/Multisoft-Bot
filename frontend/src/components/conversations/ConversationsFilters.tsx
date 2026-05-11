import { Search } from 'lucide-react';
import ChannelSelector from '@/components/shared/ChannelSelector';

interface Props {
  search: string;
  onSearchChange: (value: string) => void;
  selectedChannel: string;
  onChannelChange: (value: string) => void;
  selectedStatus: 'all' | 'open' | 'closed';
  onStatusChange: (value: 'all' | 'open' | 'closed') => void;
  channelOptions: Array<{ value: string; label: string }>;
  onClearFilters: () => void;
  showChannelSelector?: boolean;
}

export default function ConversationsFilters({
  search,
  onSearchChange,
  selectedChannel,
  onChannelChange,
  selectedStatus,
  onStatusChange,
  channelOptions,
  onClearFilters,
  showChannelSelector = true,
}: Props) {
  const hasActiveFilters = !!search.trim() || selectedChannel !== 'all' || selectedStatus !== 'all';

  return (
    <div className="flex-shrink-0 space-y-2.5 border-b border-gray-100 p-3">
      <label className="relative block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Buscar por nombre o telefono"
          className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
      </label>

      <div className={`grid grid-cols-1 gap-2 ${showChannelSelector ? 'sm:grid-cols-2' : ''}`}>
        {showChannelSelector ? (
          <ChannelSelector
            label={null}
            value={selectedChannel}
            onChange={onChannelChange}
            options={[{ value: 'all', label: 'Todos' }, ...channelOptions]}
          />
        ) : null}

        <select
          value={selectedStatus}
          onChange={(e) => onStatusChange(e.target.value as 'all' | 'open' | 'closed')}
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        >
          <option value="all">Todos los estados</option>
          <option value="open">Abiertas</option>
          <option value="closed">Cerradas</option>
        </select>
      </div>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className="text-xs font-medium text-blue-700 hover:text-blue-800"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
