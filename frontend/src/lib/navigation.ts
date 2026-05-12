import {
  LayoutDashboard,
  Building2,
  Users,
  ShieldCheck,  MessageSquare,
  Radio,
  Link2,
  Settings,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard',      label: 'Dashboard',      icon: LayoutDashboard },
  { path: '/negocios',       label: 'Negocios',       icon: Building2       },
  { path: '/admin/users',    label: 'Usuarios Globales', icon: Users        },
  { path: '/roles',          label: 'Roles',          icon: ShieldCheck     },
  { path: '/users',          label: 'Usuarios',       icon: Users           },
  { path: '/conversaciones', label: 'Conversaciones', icon: MessageSquare   },
  { path: '/canales',        label: 'Canales',        icon: Radio           },
  { path: '/integraciones',  label: 'Integraciones',  icon: Link2           },
  { path: '/configuracion',  label: 'Configuracion',  icon: Settings        },
];

const ROUTE_TITLES: Record<string, string> = Object.fromEntries([
  ['/', 'Dashboard'],
  ...NAV_ITEMS.map((item) => [item.path, item.label]),
]);

export function getPageTitle(pathname: string): string {
  if (ROUTE_TITLES[pathname]) {
    return ROUTE_TITLES[pathname];
  }

  const firstSegment = '/' + pathname.split('/').filter(Boolean)[0];
  if (firstSegment && ROUTE_TITLES[firstSegment]) {
    return ROUTE_TITLES[firstSegment];
  }

  const raw = pathname.split('/').filter(Boolean)[0] ?? '';
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}


