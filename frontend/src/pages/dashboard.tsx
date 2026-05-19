import { useEffect, useMemo, useState } from 'react';
import { Coins, Globe, LayoutDashboard, UserPlus, Users } from 'lucide-react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import StatCard from '@/components/ui/StatCard';
import { useAuthToken } from '@/hooks/useAuthToken';
import { useTenantContext } from '@/context/tenant-context';
import ChannelDistributionChart from '@/dashboard/components/ChannelDistributionChart';
import ChartCard from '@/dashboard/components/ChartCard';
import ContactsByTypeGrid from '@/dashboard/components/ContactsByTypeGrid';
import DashboardSection from '@/dashboard/components/DashboardSection';
import ErrorState from '@/dashboard/components/ErrorState';
import LoadingState from '@/dashboard/components/LoadingState';
import TenantTokenRanking from '@/dashboard/components/TenantTokenRanking';
import UsageSeriesChart from '@/dashboard/components/UsageSeriesChart';
import { useDashboardData } from '@/dashboard/hooks/useDashboardData';
import type { DashboardScope } from '@/dashboard/types';

function isSuperAdmin(userType?: string, isBackdoor?: boolean): boolean {
  return userType === 'Backdoor' || isBackdoor === true;
}

export default function DashboardPage() {
  const router = useRouter();
  const { authResolved, hasToken } = useAuthToken();
  const { user } = useTenantContext();
  const canUseGlobalScope = isSuperAdmin(user?.user_type, user?.is_backdoor);
  const [dashboardScope, setDashboardScope] = useState<DashboardScope>('tenant');
  const { data, loading, error, retry } = useDashboardData(
    dashboardScope,
    canUseGlobalScope,
    authResolved && hasToken,
  );

  useEffect(() => {
    if (!authResolved) return;
    if (!hasToken) {
      router.replace('/login');
    }
  }, [authResolved, hasToken, router]);

  useEffect(() => {
    if (!canUseGlobalScope && dashboardScope === 'global') {
      setDashboardScope('tenant');
    }
  }, [canUseGlobalScope, dashboardScope]);

  const topRowItems = useMemo(() => {
    if (!data) return [];
    return [
      {
        title: 'Usuarios totales',
        value: data.contacts.total.toLocaleString('es-AR'),
        subtitle: 'Base historica del tenant actual',
        icon: <Users className="h-5 w-5" />,
      },
      {
        title: 'Nuevos del mes',
        value: data.contacts.newThisMonth.toLocaleString('es-AR'),
        subtitle: 'Altas desde el inicio del mes',
        icon: <UserPlus className="h-5 w-5" />,
      },
      {
        title: 'Tokens consumidos',
        value: data.totalTokens.toLocaleString('es-AR'),
        subtitle: 'Consumo acumulado',
        icon: <Coins className="h-5 w-5" />,
      },
    ];
  }, [data]);

  if (!authResolved) {
    return <div className="min-h-screen bg-slate-50" />;
  }

  if (!hasToken) {
    return null;
  }

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-[1400px] space-y-6 p-4 sm:p-6 lg:space-y-8 lg:p-8">
        <PageHeader
          icon={<LayoutDashboard className="h-6 w-6" />}
          title="Dashboard operativo"
          description="Metricas en tiempo real para seguimiento de negocio y operaciones."
          actions={
            canUseGlobalScope ? (
              <Button
                variant={dashboardScope === 'global' ? 'primary' : 'secondary'}
                size="sm"
                leadingIcon={<Globe />}
                onClick={() =>
                  setDashboardScope((prev) => (prev === 'global' ? 'tenant' : 'global'))
                }
                title="Alternar vista del dashboard"
              >
                {dashboardScope === 'global' ? 'Vista global' : 'Vista tenant'}
              </Button>
            ) : null
          }
        />

        {loading ? <LoadingState cards={3} /> : null}

        {!loading && error ? <ErrorState message={error} onRetry={() => void retry()} /> : null}

        {!loading && !error && data ? (
          <div className="space-y-5 lg:space-y-6">
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {topRowItems.map((item) => (
                <StatCard
                  key={item.title}
                  title={item.title}
                  value={item.value}
                  subtitle={item.subtitle}
                  icon={item.icon}
                />
              ))}
            </section>

            {data.scope === 'tenant' ? (
              <DashboardSection
                title="Tipos de usuario"
                description="Distribucion historica por tipo con jerarquia visual y crecimiento mensual."
              >
                <ContactsByTypeGrid items={data.contactsByType} />
              </DashboardSection>
            ) : null}

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
              <ChartCard
                title="Consumo de tokens por dia"
                description="Serie temporal diaria para analizar tendencias de consumo."
              >
                <UsageSeriesChart data={data.usageSeries} />
              </ChartCard>

              {data.scope === 'tenant' ? (
                <ChartCard
                  title="Consumo por canal"
                  description="Distribucion de tokens por canal en este tenant."
                >
                  <ChannelDistributionChart data={data.tokensByChannel} />
                </ChartCard>
              ) : (
                <ChartCard
                  title="Consumo por negocio"
                  description="Ranking de tenants por consumo total de tokens."
                >
                  <TenantTokenRanking items={data.tokensByTenant} />
                </ChartCard>
              )}
            </div>

          </div>
        ) : null}
      </div>
    </AppLayout>
  );
}
