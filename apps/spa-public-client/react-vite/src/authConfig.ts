import { Configuration, LogLevel, PublicClientApplication } from '@azure/msal-browser';

const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID ?? '{tenant-id}';
const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID ?? '{client-id}';
const bffApiScope = import.meta.env.VITE_BFF_API_SCOPE ?? '{bff-api-scope}';

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: window.location.origin
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false
  },
  system: {
    loggerOptions: {
      loggerCallback: () => undefined,
      logLevel: LogLevel.Warning,
      piiLoggingEnabled: false
    }
  }
};

export const loginRequest = {
  scopes: [bffApiScope]
};

export const msalInstance = new PublicClientApplication(msalConfig);
