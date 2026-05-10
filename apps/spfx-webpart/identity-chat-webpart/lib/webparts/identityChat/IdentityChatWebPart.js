"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const sp_http_1 = require("@microsoft/sp-http");
const sp_webpart_base_1 = require("@microsoft/sp-webpart-base");
class IdentityChatWebPart extends sp_webpart_base_1.BaseClientSideWebPart {
    async render() {
        this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Creating session…</p></div>`;
        try {
            const session = await this.createSession();
            this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Session ID: ${session.session_id}</p></div>`;
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            this.domElement.innerHTML = `<div><strong>Identity Chat (SPFx)</strong><p>Session creation failed: ${message}</p></div>`;
        }
    }
    async createSession() {
        const bffBaseUrl = this.properties.bffBaseUrl?.trim() || 'http://localhost:8000';
        const bffResourceUri = this.properties.bffResourceUri?.trim() || 'api://{client-id}';
        const chatSessionEndpoint = `${bffBaseUrl.replace(/\/$/, '')}/chat/session`;
        const displayName = this.properties.displayName ?? this.context.pageContext.user?.displayName;
        // Identity invariant: display hints are never identity; the BFF's validated bearer token
        // is the sole trust anchor.
        const body = displayName ? JSON.stringify({ display_name: displayName }) : undefined;
        const client = await this.context.aadHttpClientFactory.getClient(bffResourceUri);
        const requestOptions = {
            headers: {
                traceparent: this.createTraceparent()
            }
        };
        if (body) {
            requestOptions.headers['Content-Type'] = 'application/json';
            requestOptions.body = body;
        }
        const response = await client.post(chatSessionEndpoint, sp_http_1.AadHttpClient.configurations.v1, requestOptions);
        if (!response.ok) {
            throw new Error(`BFF /chat/session failed with status ${response.status}`);
        }
        return (await response.json());
    }
    createTraceparent() {
        const traceId = this.randomHex(32);
        const spanId = this.randomHex(16);
        return `00-${traceId}-${spanId}-01`;
    }
    randomHex(length) {
        const chars = '0123456789abcdef';
        let output = '';
        for (let i = 0; i < length; i += 1) {
            output += chars[Math.floor(Math.random() * chars.length)];
        }
        return output;
    }
}
exports.default = IdentityChatWebPart;
//# sourceMappingURL=IdentityChatWebPart.js.map