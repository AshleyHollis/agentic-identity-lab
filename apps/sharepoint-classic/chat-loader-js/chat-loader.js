(() => {
  const scriptTag =
    document.currentScript ||
    document.querySelector('script[data-bff-base-url]');

  const dataset = scriptTag ? scriptTag.dataset : {};
  const options = {
    bffBaseUrl: dataset.bffBaseUrl || 'https://YOUR_BFF_DOMAIN',
    chatPath: dataset.chatPath || '/chat/session',
    theme: dataset.theme || 'light',
    containerId: dataset.containerId || 'identity-chat-root',
    userId: dataset.userId || '',
  };

  const ensureContainer = () => {
    let container = document.getElementById(options.containerId);
    if (!container) {
      container = document.createElement('div');
      container.id = options.containerId;
      document.body.appendChild(container);
    }
    container.style.border = '1px dashed #9aa0a6';
    container.style.padding = '12px';
    container.style.borderRadius = '6px';
    container.style.fontFamily =
      'Segoe UI, Roboto, Helvetica, Arial, sans-serif';
    return container;
  };

  const renderStatus = (container, message, isError = false) => {
    container.innerHTML = '';
    const status = document.createElement('div');
    status.textContent = message;
    status.style.color = isError ? '#b00020' : '#202124';
    status.style.fontSize = '14px';
    container.appendChild(status);
    return status;
  };

  const getAccessToken = async () => {
    if (
      window.IdentityChatLoader &&
      typeof window.IdentityChatLoader.getAccessToken === 'function'
    ) {
      return window.IdentityChatLoader.getAccessToken();
    }
    return null;
  };

  const buildPayload = () => ({
    // userId is a display hint only. Identity must come from access tokens.
    userId: options.userId || undefined,
    pageUrl: window.location.href,
    locale: navigator.language,
    theme: options.theme,
  });

  const start = async () => {
    const container = ensureContainer();
    renderStatus(container, 'Identity chat loader placeholder.');

    if (options.bffBaseUrl.includes('YOUR_BFF_DOMAIN')) {
      renderStatus(
        container,
        'Set data-bff-base-url to your BFF before enabling this loader.',
        true
      );
      return;
    }

    const accessToken = await getAccessToken();
    if (!accessToken) {
      renderStatus(
        container,
        'Token provider not configured. Add window.IdentityChatLoader.getAccessToken().',
        true
      );
      return;
    }

    renderStatus(container, 'Requesting chat session…');
    try {
      const response = await fetch(`${options.bffBaseUrl}${options.chatPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(buildPayload()),
      });

      if (!response.ok) {
        throw new Error(`BFF responded with ${response.status}`);
      }

      const data = await response.json();
      container.dataset.sessionId = data.sessionId || '';
      renderStatus(
        container,
        'Session created. Render your iframe or chat widget here.'
      );
    } catch (error) {
      renderStatus(
        container,
        'Unable to create session. Check BFF and token provider.',
        true
      );
      console.error('[IdentityChatLoader]', error);
    }
  };

  start();
})();
