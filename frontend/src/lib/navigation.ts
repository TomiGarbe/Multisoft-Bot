import {
  LayoutDashboard,
  Building2,
  Users,
  ShieldCheck,
  MessageSquare,
  Radio,
  Link2,
  Settings,
  type LucideIcon,
} from 'lucide-react';

export type PermissionCode = string;

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  requiredPermissions: PermissionCode[];
  backdoorOnly?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, requiredPermissions: ['analytics.read'] },
  {
    path: '/negocios',
    label: 'Negocios',
    icon: Building2,
    requiredPermissions: ['tenants.read', 'tenants.create', 'tenants.update', 'tenants.delete'],
    backdoorOnly: true,
  },
  {
    path: '/admin/users',
    label: 'Usuarios Globales',
    icon: Users,
    requiredPermissions: ['users.read', 'users.create_admin', 'users.create_backdoor'],
    backdoorOnly: true,
  },
  {
    path: '/roles',
    label: 'Roles',
    icon: ShieldCheck,
    requiredPermissions: ['roles.read', 'roles.create', 'roles.update', 'roles.delete', 'permissions.read'],
  },
  {
    path: '/users',
    label: 'Usuarios',
    icon: Users,
    requiredPermissions: ['users.read', 'users.create', 'users.update', 'users.delete'],
  },
  {
    path: '/conversaciones',
    label: 'Conversaciones',
    icon: MessageSquare,
    requiredPermissions: ['conversations.read', 'conversations.update', 'messages.read', 'messages.send'],
  },
  {
    path: '/canales',
    label: 'Canales',
    icon: Radio,
    requiredPermissions: ['channels.read', 'channels.create', 'channels.update', 'channels.delete'],
  },
  {
    path: '/integraciones',
    label: 'Integraciones',
    icon: Link2,
    requiredPermissions: ['bot_actions.read', 'bot_actions.create', 'bot_actions.update', 'bot_actions.delete'],
  },
  {
    path: '/configuracion',
    label: 'Configuracion',
    icon: Settings,
    requiredPermissions: ['channel_config.read', 'channel_config.update', 'api_keys.manage'],
  },
];

const ROUTE_TITLES: Record<string, string> = Object.fromEntries([
  ['/', 'Dashboard'],
  ...NAV_ITEMS.map((item) => [item.path, item.label]),
]);

export function getPageTitle(pathname: string): string {
  if (ROUTE_TITLES[pathname]) return ROUTE_TITLES[pathname];

  const firstSegment = '/' + pathname.split('/').filter(Boolean)[0];
  if (firstSegment && ROUTE_TITLES[firstSegment]) return ROUTE_TITLES[firstSegment];

  const raw = pathname.split('/').filter(Boolean)[0] ?? '';
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

export function canAccessSection(
  userPermissions: string[],
  section: Pick<NavItem, 'requiredPermissions' | 'backdoorOnly'>,
  isSuperAdmin = false,
): boolean {
  if (section.backdoorOnly && !isSuperAdmin) return false;
  if (section.requiredPermissions.length === 0) return true;
  const permissionSet = new Set(userPermissions);
  return section.requiredPermissions.some((permission) => permissionSet.has(permission));
}

export function canAccessPath(userPermissions: string[], pathname: string, isSuperAdmin = false): boolean {
  const section = NAV_ITEMS.find((item) => pathname === item.path || pathname.startsWith(`${item.path}/`));
  if (!section) return true;
  return canAccessSection(userPermissions, section, isSuperAdmin);
}
