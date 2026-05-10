import {
  AadHttpClient,
  AadHttpClientConfiguration,
  HttpClientResponse
} from '@microsoft/sp-http';
import { BaseClientSideWebPart } from '@microsoft/sp-webpart-base';

export interface IIdentityChatWebPartProps {
  bffBaseUrl: string;
  bffResourceUri: string;
  displayName?: string;
}

interface IChatSessionResponse {
  session_id: string;
  expires_at?: string;
}

export default class IdentityChatWebPart extends BaseClientSideWebPart<IIdentityChatWebPartProps> {
  public async render(): Promise<void> {
    this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Creating session…</p></div>`;

    try {
      const session = await this.createSession();
      this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Session ID: ${session.session_id}</p></div>`;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Session creation failed: ${message}</p></div>`;
    }
  }

  private async createSession(): Promise<IChatSessionResponse> {
    const bffBaseUrl = this.properties.bffBaseUrl?.trim() || 'http://localhost:8000';
    const bffResourceUri = this.properties.bffResourceUri?.trim() || 'api://{client-id}';
    const chatSessionEndpoint = `${bffBaseUrl.replace(/\/$/, '')}/chat/session`;

    const displayName = this.properties.displayName ?? this.context.pageContext.user?.displayName;
    // Identity invariant: display hints are never identity; the BFF's validated bearer token
    // is the sole trust anchor.
    const body = displayName ? JSON.stringify({ display_name: displayName }) : undefined;

    const client: AadHttpClient = await this.context.aadHttpClientFactory.getClient(bffResourceUri);
    const requestOptions: {
      headers: { traceparent: string; 'Content-Type'?: string };
      body?: string;
    } = {
      headers: {
        traceparent: this.createTraceparent()
      }
    };
    if (body) {
      requestOptions.headers['Content-Type'] = 'application/json';
      requestOptions.body = body;
    }

    const response: HttpClientResponse = await client.post(
      chatSessionEndpoint,
      AadHttpClient.configurations.v1 as AadHttpClientConfiguration,
      requestOptions
    );

    if (!response.ok) {
      throw new Error(`BFF /chat/session failed with status ${response.status}`);
    }

    return (await response.json()) as IChatSessionResponse;
  }

  private createTraceparent(): string {
    const traceId = this.randomHex(32);
    const spanId = this.randomHex(16);
    return `00-${traceId}-${spanId}-01`;
  }

  private randomHex(length: number): string {
    const chars = '0123456789abcdef';
    let output = '';
    for (let i = 0; i < length; i += 1) {
      output += chars[Math.floor(Math.random() * chars.length)];
    }

    return output;
  }
}
