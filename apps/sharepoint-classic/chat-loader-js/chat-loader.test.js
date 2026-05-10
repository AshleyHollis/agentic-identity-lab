const test = require('node:test');
const assert = require('node:assert/strict');

const {
  generateTraceparent,
  createMockTokenProvider,
  createChatSessionRequest,
  loadChat,
} = require('./chat-loader.js');

test('generateTraceparent returns W3C formatted value', () => {
  const traceparent = generateTraceparent();
  assert.match(traceparent, /^00-[a-f0-9]{32}-[a-f0-9]{16}-01$/);
});

test('createMockTokenProvider returns configured token', async () => {
  const provider = createMockTokenProvider('mock-token');
  const token = await provider.getAccessToken('api://{client-id}');
  assert.equal(token, 'mock-token');
});

test('createChatSessionRequest sends required headers and display_name body only', async () => {
  let requestInit;
  const fetchImpl = async (_url, init) => {
    requestInit = init;
    return {
      ok: true,
      async json() {
        return { session_id: 'abc123' };
      },
    };
  };

  await createChatSessionRequest({
    fetchImpl,
    bffBaseUrl: 'http://localhost:8000',
    sessionPath: '/chat/session',
    accessToken: 'token-value',
    traceparent: '00-0123456789abcdef0123456789abcdef-0123456789abcdef-01',
    displayName: 'Mouse',
  });

  assert.equal(requestInit.method, 'POST');
  assert.equal(requestInit.headers.Authorization, 'Bearer token-value');
  assert.equal(
    requestInit.headers.traceparent,
    '00-0123456789abcdef0123456789abcdef-0123456789abcdef-01'
  );
  assert.equal(requestInit.headers['Content-Type'], 'application/json');
  assert.equal(requestInit.body, JSON.stringify({ display_name: 'Mouse' }));
  assert.equal(Object.hasOwn(requestInit.headers, 'userId'), false);
  assert.equal(requestInit.body.includes('"userId"'), false);
});

test('loadChat uses in-memory token and does not need storage APIs', async () => {
  let called = false;
  let localStorageWrites = 0;
  let sessionStorageWrites = 0;
  global.localStorage = {
    setItem() {
      localStorageWrites += 1;
    },
  };
  global.sessionStorage = {
    setItem() {
      sessionStorageWrites += 1;
    },
  };
  try {
    const tokenProvider = {
      async getAccessToken() {
        return 'in-memory-token';
      },
    };

    const result = await loadChat({
      bffBaseUrl: 'http://localhost:8000',
      bffResourceUri: 'api://{client-id}',
      tokenProvider,
      fetchImpl: async () => {
        called = true;
        return {
          ok: true,
          async json() {
            return { session_id: 's-1' };
          },
        };
      },
    });

    assert.equal(called, true);
    assert.equal(result.session.session_id, 's-1');
    assert.equal(localStorageWrites, 0);
    assert.equal(sessionStorageWrites, 0);
  } finally {
    delete global.localStorage;
    delete global.sessionStorage;
  }
});
