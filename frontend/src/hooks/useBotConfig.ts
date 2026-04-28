import { useCallback, useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '@/services/api';

export type BotConfigPrimitive = string | number | boolean | null;
export type BotConfigObject = Record<string, BotConfigPrimitive>;
export type BotConfigArrayItem = BotConfigPrimitive | BotConfigObject;
export type BotConfigSection = BotConfigObject | BotConfigArrayItem[];

export interface BotConfig {
  identity: BotConfigObject;
  tone: BotConfigObject;
  rules: BotConfigArrayItem[];
  objectives: BotConfigArrayItem[];
  data_collection: BotConfigArrayItem[];
  [key: string]: BotConfigSection;
}

const STORAGE_KEY = 'bot_config';

const DEFAULT_CONFIG: BotConfig = {
  identity: {},
  tone: {},
  rules: [],
  objectives: [],
  data_collection: [],
};

function sanitizeConfig(raw: unknown): BotConfig {
  if (!raw || typeof raw !== 'object') {
    return { ...DEFAULT_CONFIG };
  }

  const parsed = raw as Record<string, unknown>;
  return {
    ...DEFAULT_CONFIG,
    ...parsed,
  } as BotConfig;
}

function readLocalConfig(): BotConfig {
  if (typeof window === 'undefined') {
    return { ...DEFAULT_CONFIG };
  }

  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (!saved) {
    return { ...DEFAULT_CONFIG };
  }

  try {
    return sanitizeConfig(JSON.parse(saved));
  } catch {
    return { ...DEFAULT_CONFIG };
  }
}

function writeLocalConfig(config: BotConfig) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

export function useBotConfig() {
  const [config, setConfig] = useState<BotConfig>({ ...DEFAULT_CONFIG });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await api.get('/bot-config');
        const loaded = sanitizeConfig(response.data);
        setConfig(loaded);
        writeLocalConfig(loaded);
      } catch {
        setConfig(readLocalConfig());
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const updateConfig = useCallback(async (section: string, data: BotConfigSection) => {
    let nextConfig: BotConfig = { ...DEFAULT_CONFIG };

    setConfig((prev) => {
      nextConfig = {
        ...prev,
        [section]: data,
      };
      return nextConfig;
    });

    writeLocalConfig(nextConfig);

    try {
      await api.put('/bot-config', nextConfig);
    } catch (error) {
      throw new Error(getApiErrorMessage(error, 'No se pudo guardar la configuración.'));
    }
  }, []);

  return {
    config,
    loading,
    updateConfig,
  };
}
