// Construit le dossier www/ à partir de src/index.html :
// - Three.js copié en local (le jeu marche hors ligne dans l'APK)
// - polices copiées en local, avec repli sur Google Fonts
// - retrait du point d'accès de test
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const www = path.join(root, 'www');
const nm = path.join(root, 'node_modules');

fs.rmSync(www, { recursive: true, force: true });
fs.mkdirSync(path.join(www, 'fonts'), { recursive: true });

// 1) Three.js r128
const threeSrc = path.join(nm, 'three', 'build', 'three.min.js');
if (!fs.existsSync(threeSrc)) {
  console.error('three.min.js introuvable : lance d\'abord "npm install".');
  process.exit(1);
}
fs.copyFileSync(threeSrc, path.join(www, 'three.min.js'));

// 2) Polices
const fonts = [
  ['black-ops-one', 'Black Ops One', [400]],
  ['barlow-condensed', 'Barlow Condensed', [500, 600, 700]],
];
let css = '';
for (const [pkg, family, weights] of fonts) {
  for (const w of weights) {
    const file = `${pkg}-latin-${w}-normal.woff2`;
    const src = path.join(nm, '@fontsource', pkg, 'files', file);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, path.join(www, 'fonts', file));
      css += `@font-face{font-family:'${family}';font-style:normal;font-weight:${w};font-display:swap;src:url(fonts/${file}) format('woff2')}\n`;
    } else {
      console.warn('Police manquante (repli Google Fonts) :', file);
    }
  }
}
fs.writeFileSync(path.join(www, 'fonts', 'fonts.css'), css);

// 3) HTML
let html = fs.readFileSync(path.join(root, 'src', 'index.html'), 'utf8');
const cdn = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>';
if (!html.includes(cdn)) { console.error('Balise Three.js introuvable dans src/index.html'); process.exit(1); }
html = html.replace(cdn,
  '<script src="three.min.js"></script>\n<script>if(!window.THREE)document.write(\'<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"><\\/script>\')</script>');
html = html.replace('<link rel="preconnect" href="https://fonts.googleapis.com">', '<link rel="stylesheet" href="fonts/fonts.css">\n<link rel="preconnect" href="https://fonts.googleapis.com">');
if (!process.env.KEEP_TEST) html = html.replace(/window\.__swr=\{[^\n]*\};\n/, '');
// 4) Chargeurs de modèles 3D (Mixamo FBX / glTF) et dossier models/
const libs = ['libs/fflate.min.js', 'curves/NURBSUtils.js', 'curves/NURBSCurve.js', 'loaders/FBXLoader.js', 'loaders/GLTFLoader.js', 'loaders/RGBELoader.js'];
fs.mkdirSync(path.join(www, 'lib'), { recursive: true });
let tags = '';
for (const l of libs) {
  const src = path.join(nm, 'three', 'examples', 'js', l);
  if (fs.existsSync(src)) { const name = path.basename(l); fs.copyFileSync(src, path.join(www, 'lib', name)); tags += `<script src="lib/${name}"></script>\n`; }
  else console.warn('Chargeur absent :', l);
}
html = html.replace('<script>if(!window.THREE)', tags + '<script>if(!window.THREE)');
// les chargeurs doivent venir APRÈS three.js : on déplace le bloc
html = html.replace(tags + '<script>if(!window.THREE)document.write', '<script>if(!window.THREE)document.write');
html = html.replace("<\\/script>')</script>", "<\\/script>')</script>\n" + tags);
const modelsSrc = path.join(root, 'assets', 'models');
if (fs.existsSync(modelsSrc)) fs.cpSync(modelsSrc, path.join(www, 'models'), { recursive: true });
const genSrc = path.join(root, 'assets', 'gen');
if (fs.existsSync(genSrc)) fs.cpSync(genSrc, path.join(www, 'assets', 'gen'), { recursive: true });
fs.writeFileSync(path.join(www, 'index.html'), html);

console.log('www/ prêt :', fs.readdirSync(www).join(', '));
