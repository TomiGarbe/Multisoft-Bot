import { useEffect, useState } from 'react';
import Button from '@/components/ui/Button';
import Checkbox from '@/components/ui/Checkbox';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import KeyValueEditor from '@/components/integrations/KeyValueEditor';
import type { IntegrationAuthConfig, IntegrationItem, IntegrationPayload, IntegrationTestResponse } from '@/types/integration';

interface IntegrationFormProps {
  open: boolean;
  loadingDetail: boolean;
  integration: IntegrationItem | null;
  submitting: boolean;
  canUpdate: boolean;
  onClose: () => void;
  onSave: (payload: IntegrationPayload) => Promise<void>;
  onTest: (variables: Record<string, unknown>) => Promise<IntegrationTestResponse>;
  testResult: IntegrationTestResponse | null;
}

function mapToRows(input?: Record<string, string> | null): Array<{ key: string; value: string }> {
  if (!input) return [{ key: '', value: '' }];
  const entries = Object.entries(input).map(([key, value]) => ({ key, value }));
  return entries.length > 0 ? entries : [{ key: '', value: '' }];
}

function mapToRecord(rows: Array<{ key: string; value: string }>): Record<string, string> | null {
  const next: Record<string, string> = {};
  rows.forEach((row) => {
    const key = row.key.trim();
    if (!key) return;
    next[key] = row.value;
  });
  return Object.keys(next).length > 0 ? next : null;
}

function getSafeAuthType(auth: IntegrationItem['auth_jsonb'] | null | undefined): IntegrationAuthConfig['type'] {
  if (!auth) return 'none';
  if (auth.type === 'bearer' || auth.type === 'api_key' || auth.type === 'basic' || auth.type === 'none') {
    return auth.type;
  }
  return 'none';
}

function mergeLegacyCustomAuthHeaders(
  headers: Record<string, string> | null | undefined,
  auth: IntegrationItem['auth_jsonb'] | null | undefined
): Record<string, string> | null {
  const baseHeaders = headers ?? null;
  if (!auth || auth.type !== 'custom') return baseHeaders;
  return { ...(baseHeaders ?? {}), ...auth.headers };
}

function getDefaultAuthConfig(): IntegrationAuthConfig {
  return { type: 'none' };
}

export default function IntegrationForm({
  open,
  loadingDetail,
  integration,
  submitting,
  canUpdate,
  onClose,
  onSave,
  onTest,
  testResult,
}: IntegrationFormProps) {
  const isEditing = Boolean(integration);
  const [name, setName] = useState(integration?.name ?? '');
  const [description, setDescription] = useState(integration?.description ?? '');
  const [method, setMethod] = useState(integration?.method ?? 'POST');
  const [url, setUrl] = useState(integration?.url ?? '');
  const [enabled, setEnabled] = useState(integration?.enabled ?? true);
  const [timeoutMs, setTimeoutMs] = useState(String(integration?.timeout_ms ?? ''));
  const [retryCount, setRetryCount] = useState(String(integration?.retry_count ?? ''));
  const [body, setBody] = useState(
    integration?.body_jsonb == null ? '' : typeof integration.body_jsonb === 'string' ? integration.body_jsonb : JSON.stringify(integration.body_jsonb, null, 2)
  );
  const [headers, setHeaders] = useState(mapToRows(mergeLegacyCustomAuthHeaders(integration?.headers_jsonb, integration?.auth_jsonb)));
  const [queryParams, setQueryParams] = useState(mapToRows(integration?.query_params_jsonb));
  const [authType, setAuthType] = useState<IntegrationAuthConfig['type']>(getSafeAuthType(integration?.auth_jsonb));
  const [bearerToken, setBearerToken] = useState(integration?.auth_jsonb?.type === 'bearer' ? integration.auth_jsonb.token : '');
  const [apiKeyKey, setApiKeyKey] = useState(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.key : '');
  const [apiKeyValue, setApiKeyValue] = useState(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.value : '');
  const [apiKeyLocation, setApiKeyLocation] = useState<'header' | 'query'>(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.location : 'header');
  const [basicUsername, setBasicUsername] = useState(integration?.auth_jsonb?.type === 'basic' ? integration.auth_jsonb.username : '');
  const [basicPassword, setBasicPassword] = useState(integration?.auth_jsonb?.type === 'basic' ? integration.auth_jsonb.password : '');
  const [testVariablesJson, setTestVariablesJson] = useState('{}');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(integration?.name ?? '');
    setDescription(integration?.description ?? '');
    setMethod(integration?.method ?? 'POST');
    setUrl(integration?.url ?? '');
    setEnabled(integration?.enabled ?? true);
    setTimeoutMs(String(integration?.timeout_ms ?? ''));
    setRetryCount(String(integration?.retry_count ?? ''));
    setBody(integration?.body_jsonb == null ? '' : typeof integration.body_jsonb === 'string' ? integration.body_jsonb : JSON.stringify(integration.body_jsonb, null, 2));
    setHeaders(mapToRows(mergeLegacyCustomAuthHeaders(integration?.headers_jsonb, integration?.auth_jsonb)));
    setQueryParams(mapToRows(integration?.query_params_jsonb));
    setAuthType(getSafeAuthType(integration?.auth_jsonb));
    setBearerToken(integration?.auth_jsonb?.type === 'bearer' ? integration.auth_jsonb.token : '');
    setApiKeyKey(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.key : '');
    setApiKeyValue(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.value : '');
    setApiKeyLocation(integration?.auth_jsonb?.type === 'api_key' ? integration.auth_jsonb.location : 'header');
    setBasicUsername(integration?.auth_jsonb?.type === 'basic' ? integration.auth_jsonb.username : '');
    setBasicPassword(integration?.auth_jsonb?.type === 'basic' ? integration.auth_jsonb.password : '');
    setTestVariablesJson('{}');
    setError(null);
  }, [open, integration]);

  const allowBody = method === 'POST' || method === 'PUT' || method === 'PATCH';

  const resolveAuth = (): IntegrationAuthConfig => {
    if (authType === 'bearer') return { type: 'bearer', token: bearerToken.trim() };
    if (authType === 'api_key') return { type: 'api_key', key: apiKeyKey.trim(), value: apiKeyValue, location: apiKeyLocation };
    if (authType === 'basic') return { type: 'basic', username: basicUsername.trim(), password: basicPassword };
    return getDefaultAuthConfig();
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('El nombre es obligatorio.');
      return;
    }

    if (!url.trim().startsWith('http://') && !url.trim().startsWith('https://')) {
      setError('La URL debe iniciar con http:// o https://');
      return;
    }

    let parsedBody: unknown = null;
    if (allowBody && body.trim()) {
      try {
        parsedBody = JSON.parse(body);
      } catch {
        parsedBody = body;
      }
    }

    const payload: IntegrationPayload = {
      name: name.trim(),
      description: description.trim() || null,
      enabled,
      method: method as IntegrationPayload['method'],
      url: url.trim(),
      headers_jsonb: mapToRecord(headers),
      query_params_jsonb: mapToRecord(queryParams),
      body_jsonb: allowBody ? parsedBody : null,
      variables_jsonb: [],
      auth_jsonb: resolveAuth(),
      response_config_jsonb: { response_type: 'json' },
      timeout_ms: timeoutMs.trim() ? Number(timeoutMs) : null,
      retry_count: retryCount.trim() ? Number(retryCount) : null,
    };

    await onSave(payload);
  };

  const runTestAction = async () => {
    setError(null);
    try {
      const vars = JSON.parse(testVariablesJson) as Record<string, unknown>;
      await onTest(vars);
    } catch {
      setError('Variables de prueba invalidas. Usa JSON valido.');
    }
  };

  return (
    <Modal
      isOpen={open}
      title={isEditing ? 'Editar integracion' : 'Crear integracion'}
      onClose={onClose}
      footer={
        <div className="flex items-center justify-between gap-3">
          <div>
            {isEditing ? (
              <Button type="button" variant="secondary" onClick={runTestAction} disabled={!canUpdate || submitting || !integration}>
                Probar integracion
              </Button>
            ) : null}
          </div>
          <div className="flex items-center gap-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>Cancelar</Button>
            <Button type="submit" form="integration-form" disabled={!canUpdate || submitting || loadingDetail}>
              {submitting ? 'Guardando...' : 'Guardar'}
            </Button>
          </div>
        </div>
      }
    >
      {loadingDetail ? <div className="text-sm text-slate-500">Cargando integracion...</div> : null}
      <form id="integration-form" className="space-y-5" onSubmit={submit}>
        {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}
        <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} disabled={submitting} required />
        <Input label="Descripcion" value={description} onChange={(e) => setDescription(e.target.value)} disabled={submitting} />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Metodo HTTP</label>
            <select value={method} onChange={(e) => setMethod(e.target.value as IntegrationPayload['method'])} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" disabled={submitting}>
              <option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option>
            </select>
          </div>
          <Input label="URL endpoint" value={url} onChange={(e) => setUrl(e.target.value)} disabled={submitting} required />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input label="Timeout ms" type="number" min={1} max={120000} value={timeoutMs} onChange={(e) => setTimeoutMs(e.target.value)} disabled={submitting} />
          <Input label="Retries" type="number" min={0} max={5} value={retryCount} onChange={(e) => setRetryCount(e.target.value)} disabled={submitting} />
        </div>

        <Checkbox label="Integracion activa" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />

        <div className="rounded-xl border border-slate-200 p-4 space-y-4">
          <p className="text-sm font-semibold text-slate-800">Autenticacion</p>
          <select value={authType} onChange={(e) => setAuthType(e.target.value as IntegrationAuthConfig['type'])} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" disabled={submitting}>
            <option value="none">Ninguna</option>
            <option value="bearer">Bearer token</option>
            <option value="api_key">API key</option>
            <option value="basic">Basic auth</option>
          </select>
          {authType === 'bearer' ? <Input label="Token" value={bearerToken} onChange={(e) => setBearerToken(e.target.value)} /> : null}
          {authType === 'api_key' ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Input label="Key" value={apiKeyKey} onChange={(e) => setApiKeyKey(e.target.value)} />
              <Input label="Value" value={apiKeyValue} onChange={(e) => setApiKeyValue(e.target.value)} />
              <div>
                <label className="block text-sm font-medium text-slate-700">Location</label>
                <select value={apiKeyLocation} onChange={(e) => setApiKeyLocation(e.target.value as 'header' | 'query')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  <option value="header">header</option>
                  <option value="query">query</option>
                </select>
              </div>
            </div>
          ) : null}
          {authType === 'basic' ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input label="Username" value={basicUsername} onChange={(e) => setBasicUsername(e.target.value)} />
              <Input label="Password" type="password" value={basicPassword} onChange={(e) => setBasicPassword(e.target.value)} />
            </div>
          ) : null}
        </div>

        <KeyValueEditor label="Headers" value={headers} onChange={setHeaders} disabled={submitting} />
        <KeyValueEditor label="Query params" value={queryParams} onChange={setQueryParams} disabled={submitting} />

        {allowBody ? (
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Body JSON</label>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={8} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono" placeholder='{"event":"demo"}' />
          </div>
        ) : null}

        {isEditing ? (
          <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-800">Variables de prueba (JSON)</p>
            <textarea value={testVariablesJson} onChange={(e) => setTestVariablesJson(e.target.value)} rows={4} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono" />
            {testResult ? (
              <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs">
                <p>Status: {testResult.response.status_code ?? '-'}</p>
                <p>Duracion: {testResult.timing.duration_ms} ms</p>
                <p>Resultado: {testResult.success ? 'success' : 'error'}</p>
                <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap">{JSON.stringify(testResult.response.data ?? testResult.response.text ?? testResult.error, null, 2)}</pre>
              </div>
            ) : null}
          </div>
        ) : null}
      </form>
    </Modal>
  );
}
