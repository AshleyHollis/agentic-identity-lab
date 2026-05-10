import { BaseClientSideWebPart } from '@microsoft/sp-webpart-base';
export interface IIdentityChatWebPartProps {
    bffBaseUrl: string;
    bffResourceUri: string;
    displayName?: string;
}
export default class IdentityChatWebPart extends BaseClientSideWebPart<IIdentityChatWebPartProps> {
    render(): Promise<void>;
    private createSession;
    private createTraceparent;
    private randomHex;
}
