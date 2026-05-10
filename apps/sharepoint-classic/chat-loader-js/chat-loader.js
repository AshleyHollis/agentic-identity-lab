(function classicChatLoaderFactory(globalRef) {
  const DEFAULT_SESSION_PATH = '/chat/session';

  function randomHex(byteLength) {
    const bytes = new Uint8Array(byteLength);
    const cryptoRef = globalRef.crypto || globalRef.msCrypto;

    if (cryptoRef && typeof cryptoRef.getRandomValues === 'function') {
      cryptoRef.getRandomValues(bytes);
    } else {
      for (let index = 0; index < byteLength; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
      }
    }

    let hex = '';
    for (let index = 0; index < bytes.length; index += 1) {
      hex += bytes[index].toString(16).padStart(2, '0');
    }
    return hex;
  }

  function generateTraceparent() {
    const traceId = randomHex(16);
    const spanId = randomHex(8);
    return `00-${traceId}-${spanId}-01`;
  }

  function createMockTokenProvider(mockToken) {
    return {
      async getAccessToken() {
        return mockToken || 'mock-access-token';
      },
    };
  }

  async function getSharePointProvider(pageContext) {
    const context = pageContext || globalRef._spPageContextInfo;
    if (
      !context ||
      !context.aadTokenProviderFactory ||
      typeof context.aadTokenProviderFactory.getTokenProvider !== 'function'
    ) {
      throw new Error(
        'SharePoint aadTokenProviderFactory is unavailable on this page.'
      );
    }

    const provider = await context.aadTokenProviderFactory.getTokenProvider();
    if (!provider || typeof provider.getToken !== 'function') {
      throw new Error('SharePoint token provider is unavailable.');
    }
    return provider;
  }

  function createSharePointTokenProvider(options) {
    const pageContext = options && options.pageContext;
    return {
      async getAccessToken(resourceUri) {
        const provider = await getSharePointProvider(pageContext);
        return provider.getToken(resourceUri);
      },
    };
  }

  function resolveTokenProvider(config) {
    if (config && config.tokenProvider) {
      if (typeof config.tokenProvider === 'function') {
        return {
          getAccessToken: config.tokenProvider,
        };
      }
      if (typeof config.tokenProvider.getAccessToken === 'function') {
        return config.tokenProvider;
      }
      throw new Error(
        'tokenProvider must be a function or an object with getAccessToken(resourceUri).'
      );
    }

    if (config && config.useMockTokenProvider) {
      return createMockTokenProvider(config.mockAccessToken);
    }

    return createSharePointTokenProvider(config);
  }

  async function createChatSessionRequest(config) {
    const fetchImpl = config.fetchImpl || globalRef.fetch;
    if (typeof fetchImpl !== 'function') {
      throw new Error('fetch is unavailable in this environment.');
    }

    const sessionPath = config.sessionPath || DEFAULT_SESSION_PATH;
    const body =
      config.displayName && String(config.displayName).trim().length > 0
        ? { display_name: String(config.displayName).trim() }
        : {};

    // Identity invariant: display_name is display/context only, never auth.
    const response = await fetchImpl(`${config.bffBaseUrl}${sessionPath}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${config.accessToken}`,
        traceparent: config.traceparent,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`BFF responded with ${response.status}`);
    }
    return response.json();
  }

  async function loadChat(userConfig) {
    const config = userConfig || {};
    if (!config.bffBaseUrl) {
      throw new Error('bffBaseUrl is required.');
    }
    if (!config.bffResourceUri) {
      throw new Error('bffResourceUri is required.');
    }

    const tokenProvider = resolveTokenProvider(config);
    const accessToken = await tokenProvider.getAccessToken(config.bffResourceUri);
    if (!accessToken) {
      throw new Error('Token provider returned an empty token.');
    }

    const traceparent = generateTraceparent();
    const session = await createChatSessionRequest({
      ...config,
      accessToken,
      traceparent,
    });

    return {
      session,
      traceparent,
    };
  }

  function readConfigFromDataset(docRef) {
    const documentRef = docRef || globalRef.document;
    if (!documentRef) {
      return null;
    }

    const scriptTag =
      documentRef.currentScript ||
      documentRef.querySelector('script[data-bff-base-url]');
    if (!scriptTag) {
      return null;
    }

    const dataset = scriptTag.dataset || {};
    return {
      bffBaseUrl: dataset.bffBaseUrl || '',
      bffResourceUri: dataset.bffResourceUri || '',
      sessionPath: dataset.sessionPath || DEFAULT_SESSION_PATH,
      displayName: dataset.displayName || '',
      useMockTokenProvider: dataset.tokenProvider === 'mock',
      mockAccessToken: dataset.mockAccessToken || '',
    };
  }

  const api = {
    loadChat,
    generateTraceparent,
    createMockTokenProvider,
    createSharePointTokenProvider,
    createChatSessionRequest,
    resolveTokenProvider,
    readConfigFromDataset,
  };

  globalRef.IdentityChatClassicLoader = Object.assign(
    globalRef.IdentityChatClassicLoader || {},
    api
  );

  const autoConfig = readConfigFromDataset();
  if (autoConfig && autoConfig.bffBaseUrl && autoConfig.bffResourceUri) {
    loadChat(autoConfig).catch(function handleAutoStartFailure() {
      if (typeof globalRef.console !== 'undefined') {
        globalRef.console.warn(
          '[IdentityChatClassicLoader] Unable to create chat session. Verify token provider and BFF config.'
        );
      }
    });
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : window);
