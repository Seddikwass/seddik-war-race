// Test visuel automatique : ouvre le jeu dans un vrai Chrome (rendu WebGL logiciel)
// et enregistre des captures + les erreurs console dans screens/.
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const www = path.join(__dirname, '..', 'www'), out = path.join(__dirname, '..', 'screens');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2', '.css': 'text/css', '.fbx': 'application/octet-stream', '.glb': 'model/gltf-binary' };
const srv = http.createServer((q, r) => { let f = path.join(www, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(8099);
const log = [];
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', e => log.push('PAGEERROR ' + e.message));
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') log.push(m.type().toUpperCase() + ' ' + m.text()); });
  await pg.goto('http://localhost:8099/index.html'); await pg.waitForTimeout(4000);
  await pg.screenshot({ path: path.join(out, '01-menu.png') });
  await pg.click('[data-act=garage]'); await pg.waitForTimeout(2500); await pg.screenshot({ path: path.join(out, '02-garage.png') });
  await pg.click('#garage [data-act=back]');
  const runs = [['k17', 'day', 'muscle'], ['refinery', 'night', 'proto'], ['docks', 'rain', 'rally'], ['coast', 'day', 'phoenix']];
  let n = 3;
  for (const [track, wx, car] of runs) {
    await pg.evaluate(([track, wx, car]) => { __swr.startRace({ quick: true, t: 'Test', ot: 'Test', laps: 3, opp: [0, 1, 2, 3, 4], skill: .9, track, wx, car }); __swr.race.P.auto = true; }, [track, wx, car]);
    await pg.waitForTimeout(16000);
    await pg.screenshot({ path: path.join(out, `0${n++}-${track}-${wx}.png`) });
    const info = await pg.evaluate(() => { const r = __swr.race; return { t: r.t.toFixed(1), idx: r.P.idx, spd: Math.round(r.P.speed * 3.6) }; });
    log.push(`RACE ${track}/${wx}: ${JSON.stringify(info)}`);
  }
  await pg.keyboard.press('KeyC'); await pg.waitForTimeout(1500); await pg.screenshot({ path: path.join(out, '07-camera-proche.png') });
  await pg.keyboard.press('KeyC'); await pg.waitForTimeout(1500); await pg.screenshot({ path: path.join(out, '08-camera-capot.png') });
  const ri = await pg.evaluate(() => { try { return JSON.stringify(document.querySelector('canvas') ? 'ok' : 'no canvas'); } catch (e) { return e.message; } });
  log.push('CANVAS ' + ri);
  fs.writeFileSync(path.join(out, 'log.txt'), log.join('\n') + '\n');
  await b.close(); srv.close();
})().catch(e => { fs.writeFileSync(path.join(out, 'log.txt'), log.join('\n') + '\nFATAL ' + e.stack); srv.close(); process.exit(0); });
