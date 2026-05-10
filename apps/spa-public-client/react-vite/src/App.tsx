import { useMemo, useState } from 'react';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import { createChatSession } from './bffClient';

const App = () => {
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const [displayName, setDisplayName] = useState('');
  const [sessionResult, setSessionResult] = useState('');
  const [error, setError] = useState('');

  const activeAccount = useMemo(() => {
    return accounts[0] ?? null;
  }, [accounts]);

  const signIn = async () => {
    setError('');
    await instance.loginPopup(loginRequest);
  };

  const signOut = async () => {
    setSessionResult('');
    setError('');
    await instance.logoutPopup();
  };

  const startSession = async () => {
    if (!activeAccount) {
      setError('Sign in first.');
      return;
    }

    try {
      const tokenResult = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount
      });

      if (!tokenResult.accessToken) {
        throw new Error('No access token returned by MSAL.');
      }

      const session = await createChatSession({
        accessToken: tokenResult.accessToken,
        displayName: displayName || undefined
      });

      setSessionResult(`Session ready: ${session.session_id}`);
      setError('');
    } catch (caughtError) {
      if (caughtError instanceof InteractionRequiredAuthError) {
        const popupResult = await instance.acquireTokenPopup({
          ...loginRequest,
          account: activeAccount
        });

        const session = await createChatSession({
          accessToken: popupResult.accessToken,
          displayName: displayName || undefined
        });

        setSessionResult(`Session ready: ${session.session_id}`);
        setError('');
        return;
      }

      const message =
        caughtError instanceof Error ? caughtError.message : 'Unknown error';
      setError(message);
    }
  };

  return (
    <main style={{ fontFamily: 'Segoe UI, sans-serif', padding: '24px', maxWidth: '760px' }}>
      <h1>Identity Lab SPA (React + Vite)</h1>
      <p>
        Public-client placeholder for M7. Browser acquires delegated token via MSAL
        PKCE, then calls the BFF only.
      </p>

      {!isAuthenticated ? (
        <button type="button" onClick={signIn}>
          Sign in with popup
        </button>
      ) : (
        <div style={{ display: 'grid', gap: '12px' }}>
          <p>
            Signed in as <strong>{activeAccount?.username ?? 'unknown user'}</strong>
          </p>
          <label>
            Display name (optional):
            <input
              type="text"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Display-only value"
              style={{ marginLeft: '8px' }}
            />
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button type="button" onClick={startSession}>
              Start BFF session
            </button>
            <button type="button" onClick={signOut}>
              Sign out
            </button>
          </div>
        </div>
      )}

      <p>
        <strong>Identity rule:</strong> Any <code>userId</code>/<code>display_name</code> body
        field is display-only. Trust comes from bearer token validation at the BFF.
      </p>

      {sessionResult ? <p>{sessionResult}</p> : null}
      {error ? <p style={{ color: '#b00020' }}>{error}</p> : null}
    </main>
  );
};

export default App;
