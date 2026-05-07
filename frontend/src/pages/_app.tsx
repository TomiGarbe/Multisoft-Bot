import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { TenantProvider } from '@/context/tenant-context';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Multisoft Bot</title>
        <meta name="description" content="Multisoft Bot admin panel" />
      </Head>
      <TenantProvider>
        <Component {...pageProps} />
      </TenantProvider>
    </>
  );
}
