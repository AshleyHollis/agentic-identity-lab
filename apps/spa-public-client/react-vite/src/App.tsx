const App = () => {
  return (
    <main style={{ fontFamily: 'Segoe UI, sans-serif', padding: '24px' }}>
      <h1>Identity Lab SPA (React + Vite)</h1>
      <p>
        This is a placeholder UI for comparing public-client token acquisition
        flows. It does not implement authentication.
      </p>
      <ol>
        <li>Acquire an access token via an approved public-client library.</li>
        <li>Call the BFF with Authorization: Bearer &lt;token&gt;.</li>
        <li>
          Send <code>userId</code> only as a display hint; identity comes from
          validated tokens.
        </li>
      </ol>
    </main>
  );
};

export default App;
