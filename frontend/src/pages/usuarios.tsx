import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import UsersForm from '@/components/users/UsersForm';
import UsersTable from '@/components/users/UsersTable';
import { useUsuarios } from '@/hooks/useUsuarios';

export default function UsersPage() {
  const toast = useToast();
  const {
    hasToken,
    usuarios,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedUsuario,
    createUsuario,
    updateUsuario,
    deleteUsuario,
    statusLabel,
    setIsFormOpen,
    fetchUsuarios,
  } = useUsuarios(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          title="Usuarios"
          description="Gestiona los usuarios asociados a cada negocio."
          actions={<Button onClick={createUsuario}>+ Crear usuario</Button>}
        />

        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        {loading ? (
          <div className="text-center text-sm text-slate-500">Cargando usuarios...</div>
        ) : (
          <UsersTable
            users={usuarios}
            isDeletingId={deletingId}
            onEdit={updateUsuario}
            onDelete={deleteUsuario}
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
