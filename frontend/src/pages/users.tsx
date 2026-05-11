import AppLayout from '@/components/layout/AppLayout';
import UsersForm from '@/components/users/UsersForm';
import UsersTable from '@/components/users/UsersTable';
import Button from '@/components/ui/Button';
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
          title="Usuarios"
          description="Administra los usuarios del negocio: accesos, roles y estado de cuenta."
          actions={<Button onClick={createUsuario}>+ Crear usuario</Button>}
        />

        {error ? <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}

        {loading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
            Cargando usuarios...
          </div>
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
