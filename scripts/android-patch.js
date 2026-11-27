// Après "npx cap add android" : jeu en paysage et en plein écran.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const manifest = path.join(root, 'android', 'app', 'src', 'main', 'AndroidManifest.xml');
if (!fs.existsSync(manifest)) { console.error('Dossier android/ absent : lance "npx cap add android" avant.'); process.exit(1); }
let xml = fs.readFileSync(manifest, 'utf8');
if (!xml.includes('android:screenOrientation')) {
  xml = xml.replace(/<activity\b/, '<activity\n            android:screenOrientation="sensorLandscape"');
}
fs.writeFileSync(manifest, xml);

const styles = path.join(root, 'android', 'app', 'src', 'main', 'res', 'values', 'styles.xml');
if (fs.existsSync(styles)) {
  let s = fs.readFileSync(styles, 'utf8');
  if (!s.includes('android:windowFullscreen')) {
    s = s.replace(/(<style name="AppTheme.NoActionBar"[^>]*>)/, '$1\n        <item name="android:windowFullscreen">true</item>');
    fs.writeFileSync(styles, s);
  }
}
console.log('AndroidManifest et styles mis à jour (paysage, plein écran).');
