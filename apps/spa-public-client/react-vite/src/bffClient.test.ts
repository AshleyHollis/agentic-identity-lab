import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createChatSession } from './bffClient';

describe('createChatSession', () => {
  beforeEach(() => {
    vi.stubGlobal('crypto', {
      getRandomValues: <T extends Uint8Array>(array: T): T => {
        array.fill(7);
        return array;
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('sends Authorization bearer token and traceparent headers to the BFF', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ session_id: 'session-123' })
    });
    vi.stubGlobal('fetch', fetchMock);

    await createChatSession({
      accessToken: 'token-value',
      displayName: 'Display Name'
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, options] = fetchMock.mock.calls[0] as [
      string,
      { headers: Record<string, string>; body: string }
    ];

    expect(options.headers.Authorization).toBe('Bearer token-value');
    expect(options.headers.traceparent).toMatch(/^00-[a-f0-9]{32}-[a-f0-9]{16}-01$/);
    expect(options.body).toContain('"display_name":"Display Name"');
  });

  it('propagates a 401 when no usable bearer token is provided', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      createChatSession({
        accessToken: '',
        displayName: 'No Token User'
      })
    ).rejects.toThrow('401');
  });
});
