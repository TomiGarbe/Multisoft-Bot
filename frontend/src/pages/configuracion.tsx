import { useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import GeneralSettingsSection from '@/components/settings/GeneralSettingsSection';
import IntegrationsSettingsSection from '@/components/settings/IntegrationsSettingsSection';
import SecuritySettingsSection from '@/components/settings/SecuritySettingsSection';
import SettingsTabs from '@/components/settings/SettingsTabs';
import ChannelSelector from '@/components/shared/ChannelSelector';
import { useSettingsPage } from '@/hooks/useSettingsPage';

const tabs = [
  { key: 'general', label: 'General' },
  { key: 'integrations', label: 'Integraciones' },
  { key: 'security', label: 'Seguridad' },
];

export default function ConfiguracionPage() {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('general');
  const settings = useSettingsPage(toast);

  if (!settings.hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="flex h-full min-h-0 flex-col overflow-hidden">
        <div className="shrink-0 px-6 pt-6 md:px-8 md:pt-8">
          <PageHeader
            title="Configuracion"
            description="Configuracion operativa, comportamiento AI y seguridad webhook por canal."
          />
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-6 md:px-8 md:pb-8">
          <div className="space-y-6">
            <SettingsTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <ChannelSelector
                label="Alcance de configuracion"
                value={settings.selectedChannelId ?? ''}
                options={settings.channelOptions}
                onChange={settings.handleChannelChange}
                disabled={settings.channelsLoading || !settings.channelOptions.length}
                placeholder="Sin canales disponibles"
              />
              <p className="mt-2 text-xs text-slate-500">
                {settings.isAllChannelsSelected
                  ? 'Estas editando configuracion global para todos los canales.'
                  : `Estas editando solo ${settings.selectedChannel?.name ?? 'el canal seleccionado'}.`}
              </p>
            </section>

            {settings.channelsLoading || settings.loadingChannelConfig ? (
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">Cargando configuracion...</div>
            ) : null}

            {activeTab === 'general' ? (
              <GeneralSettingsSection
                scopeLabel={settings.isAllChannelsSelected ? 'Todos los canales' : settings.selectedChannel?.name ?? 'Canal'}
                channelSettings={settings.channelSettings}
                userTypes={settings.userTypes}
                botConfig={settings.channelConfig}
                onChannelSettingsChange={settings.updateChannelSettings}
                onUserTypesChange={settings.updateUserTypes}
                onBotConfigChange={settings.updateConfigState}
                onSaveChannelConfig={() => void settings.saveChannel()}
                isChannelDirty={settings.isChannelDirty}
                savingChannel={settings.savingChannelConfig}
                statusText={settings.status.is_valid ? 'Configuracion AI valida.' : `Faltan campos: ${settings.missingFields.join(', ') || 'revisar identidad y reglas'}.`}
              />
            ) : null}

            {activeTab === 'security' ? (
              <SecuritySettingsSection
                channels={settings.channels}
                apiKeys={settings.apiKeys}
                loading={settings.apiKeysLoading}
                saving={settings.apiKeysSaving}
                onCreate={settings.createWebhookApiKey}
                onRegenerate={settings.regenerateWebhookApiKey}
                onDeactivate={settings.deactivateWebhookApiKey}
                onDelete={settings.deleteWebhookApiKey}
              />
            ) : null}

            {activeTab === 'integrations' ? (
              <IntegrationsSettingsSection
                items={settings.integrations}
                selectedActionIds={settings.selectedIntegrationIds}
                mixedActionIds={settings.mixedIntegrationIds}
                scopeLabel={settings.isAllChannelsSelected ? 'Todos los canales' : settings.selectedChannel?.name ?? 'Canal'}
                loading={settings.integrationsLoading}
                saving={settings.integrationsSaving}
                dirty={settings.isIntegrationsDirty}
                onToggle={settings.toggleIntegration}
                onSave={() => void settings.saveIntegrations()}
              />
            ) : null}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
