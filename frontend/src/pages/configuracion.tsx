import { useState } from 'react';
import { Cable, Filter, Settings, ShieldCheck, Sliders } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Card from '@/components/ui/Card';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import GeneralSettingsSection from '@/components/settings/GeneralSettingsSection';
import IntegrationsSettingsSection from '@/components/settings/IntegrationsSettingsSection';
import SecuritySettingsSection from '@/components/settings/SecuritySettingsSection';
import SettingsTabs from '@/components/settings/SettingsTabs';
import ChannelSelector from '@/components/shared/ChannelSelector';
import { useSettingsPage } from '@/hooks/useSettingsPage';

const tabs = [
  { key: 'general', label: 'General', icon: <Sliders /> },
  { key: 'integrations', label: 'Integraciones', icon: <Cable /> },
  { key: 'security', label: 'Seguridad', icon: <ShieldCheck /> },
];

export default function ConfiguracionPage() {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('general');
  const settings = useSettingsPage(toast);

  if (!settings.authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!settings.hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="flex h-full min-h-0 flex-col overflow-hidden">
        <div className="shrink-0 px-6 pt-6 md:px-8 md:pt-8">
          <PageHeader
            icon={<Settings className="h-6 w-6" />}
            title="Configuracion"
            description="Configuracion operativa, comportamiento AI y seguridad webhook por canal."
          />
        </div>

        <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-6 md:px-8 md:pb-8">
          <div className="space-y-6">
            <SettingsTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

            <Card
              icon={<Filter className="h-5 w-5" />}
              title="Alcance de configuracion"
              description={
                settings.isAllChannelsSelected
                  ? 'Estas editando configuracion global para todos los canales.'
                  : `Estas editando solo ${settings.selectedChannel?.name ?? 'el canal seleccionado'}.`
              }
              padding="md"
            >
              <ChannelSelector
                label={null}
                value={settings.selectedChannelId ?? ''}
                options={settings.channelOptions}
                onChange={settings.handleChannelChange}
                disabled={settings.channelsLoading || !settings.channelOptions.length}
                placeholder="Sin canales disponibles"
              />
            </Card>

            {settings.channelsLoading || settings.loadingChannelConfig ? (
              <EmptyState
                title="Cargando configuracion..."
                description="Obteniendo los ajustes para el alcance seleccionado."
                compact
              />
            ) : null}

            {activeTab === 'general' ? (
              <GeneralSettingsSection
                scopeLabel={
                  settings.isAllChannelsSelected
                    ? 'Todos los canales'
                    : settings.selectedChannel?.name ?? 'Canal'
                }
                channelSettings={settings.channelSettings}
                userTypes={settings.userTypes}
                botConfig={settings.channelConfig}
                onChannelSettingsChange={settings.updateChannelSettings}
                onUserTypesChange={settings.updateUserTypes}
                onBotConfigChange={settings.updateConfigState}
                onSaveChannelConfig={() => void settings.saveChannel()}
                isChannelDirty={settings.isChannelDirty}
                savingChannel={settings.savingChannelConfig}
                statusText={
                  settings.status.is_valid
                    ? 'Configuracion AI valida.'
                    : `Faltan campos: ${settings.missingFields.join(', ') || 'revisar identidad y reglas'}.`
                }
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
                scopeLabel={
                  settings.isAllChannelsSelected
                    ? 'Todos los canales'
                    : settings.selectedChannel?.name ?? 'Canal'
                }
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
