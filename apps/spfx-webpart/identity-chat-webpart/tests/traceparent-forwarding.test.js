const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

test('SPFx web part configures AadHttpClient with traceparent request header', () => {
  const sourcePath = path.join(
    __dirname,
    '..',
    'src',
    'webparts',
    'identityChat',
    'IdentityChatWebPart.ts'
  );
  const source = fs.readFileSync(sourcePath, 'utf8');

  assert.match(source, /aadHttpClientFactory\.getClient\(bffResourceUri\)/);
  assert.match(
    source,
    /requestOptions[\s\S]*headers:\s*\{[\s\S]*traceparent:\s*this\.createTraceparent\(\)/
  );
  assert.match(source, /client\.post\([\s\S]*requestOptions[\s\S]*\)/);
  assert.doesNotMatch(source, /\buserId\b/);
  assert.match(source, /JSON\.stringify\(\{\s*display_name:\s*displayName\s*\}\)/);
});
