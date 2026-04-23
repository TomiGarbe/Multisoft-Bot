'use client';

import AppLayout from '@/components/layout/AppLayout';
import UserForm from '@/components/users/UserForm';
import Button from '@/components/ui/Button';
import { ToastViewport, useToast } from '@/components/ui/toast';
import UsersTable from '@/components/users/UsersTable';
import { useUsersPage } from '@/hooks/users/useUsersPage';

export default function UsersPage() {
  const toast = useToast();

  const {
    hasToken,
    users,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedUser,
    openCreate,
    openEdit,
    handleDelete,
    statusLabel,
    setIsFormOpen,
    loadUsers,
  } = useUsersPage(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <section className="flex flex-col items-start justify-between gap-4 rounded-2xl border bg-white p-6 shadow-sm md:flex-row md:items-center">
          <div>
            <h1 className="text-3xl font-bold">Users</h1>
            <p className="mt-2 text-sm text-slate-600">
              Create, update and remove tenant users.
            </p>
          </div>

          <Button onClick={openCreate}>+ Create User</Button>
        </section>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="text-center text-sm text-slate-500">
            Loading users...
          </div>
        ) : (
          <UsersTable
            users={users}
            isDeletingId={isDeletingId}
            onEdit={openEdit}
            onDelete={handleDelete}
            statusLabel={statusLabel}
          />
        )}
      </div>

      <UserForm
        isOpen={isFormOpen}
        user={selectedUser}
        onClose={() => setIsFormOpen(false)}
        onSaved={(message) => {
          toast.success(message);
          void loadUsers();
        }}
      />
    </AppLayout>
  );
}