const { series } = require('gulp');
const { execSync } = require('node:child_process');

function clean(done) {
  execSync('node -e "require(\'fs\').rmSync(\'lib\', { recursive: true, force: true })"', { stdio: 'inherit' });
  done();
}

function build(done) {
  execSync('npm run build:ts', { stdio: 'inherit' });
  done();
}

exports.clean = clean;
exports.build = series(clean, build);
