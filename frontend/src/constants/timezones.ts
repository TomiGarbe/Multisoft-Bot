export const DEFAULT_TENANT_TIMEZONE = 'America/Argentina/Cordoba';

export type TenantTimezoneOption = {
  value: string;
  label: string;
};

export const TENANT_TIMEZONE_OPTIONS: TenantTimezoneOption[] = [
  { value: 'America/Argentina/Cordoba', label: 'Argentina - Cordoba' },
  { value: 'America/Argentina/Buenos_Aires', label: 'Argentina - Buenos Aires' },
  { value: 'America/Santiago', label: 'Chile - Santiago' },
  { value: 'America/Montevideo', label: 'Uruguay - Montevideo' },
  { value: 'America/Sao_Paulo', label: 'Brasil - Sao Paulo' },
  { value: 'America/Asuncion', label: 'Paraguay - Asuncion' },
  { value: 'America/Lima', label: 'Peru - Lima' },
  { value: 'America/Bogota', label: 'Colombia - Bogota' },
  { value: 'America/Mexico_City', label: 'Mexico - Ciudad de Mexico' },
  { value: 'America/La_Paz', label: 'Bolivia - La Paz' },
];

export const TENANT_TIMEZONE_VALUES = new Set(TENANT_TIMEZONE_OPTIONS.map((option) => option.value));

export const TENANT_TIMEZONE_LABEL_BY_VALUE: Record<string, string> = Object.fromEntries(
  TENANT_TIMEZONE_OPTIONS.map((option) => [option.value, option.label]),
);

export function isAllowedTenantTimezone(value: string): boolean {
  return TENANT_TIMEZONE_VALUES.has(value);
}

export function resolveTenantTimezone(value: string | null | undefined): string {
  if (value && isAllowedTenantTimezone(value)) return value;
  return DEFAULT_TENANT_TIMEZONE;
}
