import { Plus, Users } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import UsersForm from '@/components/users/UsersForm';
import UsersTable from '@/components/users/UsersTable';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { useUsers } from '@/hooks/useUsers';

export default function UsersPage() {
  const toast = useToast();
  const {
    hasToken,
    usuarios,
    loading,
    error,
    deletingId,
    updatingId,
    isFormOpen,
    selectedUsuario,
    createUsuario,
    updateUsuario,
    deleteUsuario,
    toggleUsuarioEstado,
    resetUsuarioPassword,
    setIsFormOpen,
    fetchUsuarios,
    statusLabel,
  } = useUsers(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<Users className="h-6 w-6" />}
          title="Usuarios"
          description="Administra los usuarios del negocio: accesos, roles y estado de cuenta."
          actions={
            <Button leadingIcon={<Plus />} onClick={createUsuario}>
              Crear usuario
            </Button>
          }
        />

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <EmptyState title="Cargando usuarios..." description="Obteniendo la lista." compact />
        ) : (
          <UsersTable
            users={usuarios}
            isDeletingId={deletingId}
            isUpdatingId={updatingId}
            onEdit={updateUsuario}
            onDelete={deleteUsuario}
            onToggleStatus={toggleUsuarioEstado}
            onResetPassword={resetUsuarioPassword}
            statusLabel={statusLabel}
          />
        )}
      </div>

      <UsersForm
        isOpen={isFormOpen}
        user={selectedUsuario}
        onClose={() => setIsFormOpen(false)}
        onSaved={(message) => {
          toast.success(message);
          void fetchUsuarios();
        }}
      />
    </AppLayout>
  );
}
