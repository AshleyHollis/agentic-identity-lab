type CreateChatSessionInput = {
  accessToken: string;
  displayName?: string;
};

type ChatSessionResponse = {
  session_id: string;
  expires_at?: string;
};

const normalizeBaseUrl = (baseUrl: string): string => {
  return baseUrl.replace(/\/+$/, '');
};

const createHex = (length: number): string => {
  const bytes = crypto.getRandomValues(new Uint8Array(length / 2));
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
};

export const createTraceparent = (): string => {
  return `00-${createHex(32)}-${createHex(16)}-01`;
};

export const createChatSession = async (
  input: CreateChatSessionInput
): Promise<ChatSessionResponse> => {
  const bffBaseUrl = import.meta.env.VITE_BFF_BASE_URL ?? 'http://localhost:8000';
  const response = await fetch(
    `${normalizeBaseUrl(bffBaseUrl)}/chat/session`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${input.accessToken}`,
        'Content-Type': 'application/json',
        traceparent: createTraceparent()
      },
      // Identity invariant: userId/display fields are never identity; BFF bearer token validation is the trust anchor.
      body: JSON.stringify({ display_name: input.displayName ?? null })
    }
  );

  if (!response.ok) {
    throw new Error(`BFF session request failed (${response.status}).`);
  }

  return (await response.json()) as ChatSessionResponse;
};
