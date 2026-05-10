export default function Page() {
  return (
    <main style={{ fontFamily: 'Segoe UI, sans-serif', padding: '24px' }}>
      <h1>Identity Lab SPA (Next.js)</h1>
      <p>
        Placeholder UI for comparing public-client token acquisition options.
        This page does not implement authentication.
      </p>
      <ul>
        <li>Acquire access tokens with an approved library.</li>
        <li>Send Authorization: Bearer &lt;token&gt; to the BFF.</li>
        <li>
          <code>userId</code> is a display hint only; identity comes from
          validated tokens.
        </li>
      </ul>
    </main>
  );
}
