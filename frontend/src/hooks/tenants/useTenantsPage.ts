import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/services/auth';
import { getApiErrorMessage } from '@/services/api';
import {
  getTenants,
  deleteTenant,
} from '@/services/tenants';
import type { Tenant } from '@/types/tenant';

export function useTenantsPage(toast: any) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  const loadTenants = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await getTenants();
      setTenants(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load tenants.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void loadTenants();
  }, [hasToken, loadTenants]);

  const openCreate = () => {
    setSelectedTenant(null);
    setIsFormOpen(true);
  };

  const openEdit = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setIsFormOpen(true);
  };

  const handleDelete = async (tenant: Tenant) => {
    const confirmed = window.confirm(
      `Delete tenant "${tenant.name}"? This action cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      setIsDeletingId(tenant.id);
      await deleteTenant(tenant.id);
      toast.success('Tenant deleted successfully.');
      await loadTenants();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Unable to delete tenant.'));
    } finally {
      setIsDeletingId(null);
    }
  };

  return {
    hasToken,
    tenants,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedTenant,
    openCreate,
    openEdit,
    handleDelete,
    setIsFormOpen,
    loadTenants,
  };
}