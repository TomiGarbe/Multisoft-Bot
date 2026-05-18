import type { ReactNode } from 'react';
import Select from '@/components/ui/Select';

export interface ChannelSelectorOption {
  value: string;
  label: string;
}

interface ChannelSelectorProps {
  label?: ReactNode;
  value: string;
  options: ChannelSelectorOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export default function ChannelSelector({
  label = 'Canal',
  value,
  options,
  onChange,
  disabled,
  placeholder = 'Seleccionar canal',
  className = '',
}: ChannelSelectorProps) {
  return (
    <div className={className}>
      <Select
        label={typeof label === 'string' ? label : undefined}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        options={options}
        placeholder={!options.length ? placeholder : undefined}
      />
    </div>
  );
}
