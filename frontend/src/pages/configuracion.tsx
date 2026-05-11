import { useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import AdvancedSettingsSection from '@/components/settings/AdvancedSettingsSection';
import AssistantSettingsSection from '@/components/settings/AssistantSettingsSection';
import ChannelSettingsSection from '@/components/settings/ChannelSettingsSection';
import GeneralSettingsSection from '@/components/settings/GeneralSettingsSection';
import IntegrationsSettingsSection from '@/components/settings/IntegrationsSettingsSection';
import SecuritySettingsSection from '@/components/settings/SecuritySettingsSection';
import SettingsTabs from '@/components/settings/SettingsTabs';
import ChannelSelector from '@/components/shared/ChannelSelector';
import { useSettingsPage } from '@/hooks/useSettingsPage';

const tabs = [
  { key: 'general', label: 'General' },
  { key: 'assistant', label: 'IA / Asistente' },
  { key: 'channels', label: 'Canales' },
  { key: 'integrations', label: 'Integraciones' },
  { key: 'security', label: 'Seguridad' },
  { key: 'advanced', label: 'Avanzado' },
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
            description="Configuracion organizada por negocio, asistente, canales e integraciones."
          />
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-6 md:px-8 md:pb-8">
          <div className="space-y-6">
            <SettingsTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

            {(activeTab === 'assistant' || activeTab === 'channels' || activeTab === 'integrations') ? (
              <section className="rounded-xl border border-slate-200 bg-white p-4">
                <ChannelSelector
                  value={settings.selectedChannelId ?? ''}
                  options={settings.channelOptions}
                  onChange={settings.handleChannelChange}
                  disabled={settings.channelsLoading || !settings.channels.length}
                  placeholder="Sin canales disponibles"
                />
              </section>
            ) : null}

            {settings.channelsLoading || settings.loadingChannelConfig ? (
              <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">Cargando configuracion...</div>
            ) : null}

            {activeTab === 'general' ? (
              <GeneralSettingsSection
                value={settings.tenantSettings}
                onChange={settings.updateTenantSettings}
                onSave={() => void settings.saveTenant()}
                isDirty={settings.isTenantDirty}
                saving={settings.savingTenantSettings}
              />
            ) : null}

            {activeTab === 'assistant' ? (
              <AssistantSettingsSection value={settings.channelConfig} onChange={settings.updateConfigState} />
            ) : null}

            {activeTab === 'channels' ? (
              <ChannelSettingsSection
                channel={settings.selectedChannel}
                value={settings.channelSettings}
                userTypes={settings.userTypes}
                status={settings.status}
                missingFields={settings.missingFields}
                isDirty={settings.isChannelDirty}
                saving={settings.savingChannelConfig}
                onSave={() => void settings.saveChannel()}
                onChannelSettingsChange={settings.updateChannelSettings}
                onUserTypesChange={settings.updateUserTypes}
              />
            ) : null}

            {activeTab === 'integrations' ? <IntegrationsSettingsSection channel={settings.selectedChannel} /> : null}
            {activeTab === 'security' ? <SecuritySettingsSection /> : null}
            {activeTab === 'advanced' ? <AdvancedSettingsSection /> : null}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
