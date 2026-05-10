import { describe, expect, it } from 'vitest';
import { loginRequest, msalConfig } from './authConfig';

describe('msalConfig', () => {
  it('uses sessionStorage and disables cookie auth state', () => {
    expect(msalConfig.cache?.cacheLocation).toBe('sessionStorage');
    expect(msalConfig.cache?.cacheLocation).not.toBe('localStorage');
    expect(msalConfig.cache?.storeAuthStateInCookie).toBe(false);
  });

  it('uses a delegated scope placeholder, not .default', () => {
    expect(loginRequest.scopes[0]).toBeDefined();
    expect(loginRequest.scopes[0]).not.toContain('.default');
  });
});
