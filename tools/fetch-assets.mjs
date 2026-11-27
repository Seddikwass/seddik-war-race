// Télécharge des ressources CC0 de Poly Haven (ciels HDRI + textures PBR) dans assets/gen/
// Lancé par GitHub Actions (accès Internet). Licence : CC0 (domaine public).
import fs from 'node:fs'; import path from 'node:path';
const OUT = path.join(process.cwd(), 'assets', 'gen'); fs.mkdirSync(OUT, { recursive: true });
const UA = { headers: { 'User-Agent': 'SeddikWarRace-build/1.0 (github.com/Seddikwass/seddik-war-race)' } };
const api = async u => { const r = await fetch('https://api.polyhaven.com' + u, UA); if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); };
const dl = async (url, file) => { const r = await fetch(url, UA); if (!r.ok) throw new Error(url + ' ' + r.status); fs.writeFileSync(path.join(OUT, file), Buffer.from(await r.arrayBuffer())); return file; };
const WANT = {
  hdris: {
    day: { prefer: ['industrial_sunset_02_puresky', 'industrial_sunset_puresky', 'kloofendal_48d_partly_cloudy_puresky', 'qwantani_sunset_puresky'], tags: ['sunset', 'clear'] },
    rain: { prefer: ['kloofendal_overcast_puresky', 'overcast_soil_puresky', 'cloudy_vondelpark'], tags: ['overcast', 'cloudy'] },
    night: { prefer: ['moonless_golf', 'dikhololo_night', 'satara_night'], tags: ['night'] },
    show: { prefer: ['industrial_workshop_foundry', 'old_depot', 'abandoned_garage', 'machine_shop_02'], tags: ['industrial', 'indoor'] },
  },
  textures: {
    asphalt: { prefer: ['asphalt_02', 'asphalt_04', 'asphalt_track', 'asphalt_01'], tags: ['asphalt', 'road'] },
    concrete: { prefer: ['concrete_wall_008', 'concrete_floor_02', 'concrete_wall_004', 'concrete_pavement'], tags: ['concrete'] },
    ground: { prefer: ['dry_ground_01', 'brown_mud_02', 'aerial_ground_rock', 'gravelly_sand'], tags: ['ground', 'dirt'] },
    rock: { prefer: ['rock_face', 'rocky_terrain_02', 'rock_wall_08', 'aerial_rocks_02'], tags: ['rock'] },
    metal: { prefer: ['rusty_metal_02', 'metal_plate', 'rusty_metal_sheet', 'corrugated_iron'], tags: ['metal'] },
  },
};
const manifest = { hdris: {}, textures: {}, credits: [] };
const pick = (list, want) => want.prefer.find(id => list[id]) || Object.keys(list).find(id => want.tags.some(t => (list[id].tags || []).concat(list[id].categories || []).join(' ').includes(t)));
const credit = (id, info) => manifest.credits.push({ id, name: info.name, authors: Object.keys(info.authors || {}), license: 'CC0', url: 'https://polyhaven.com/a/' + id });
const hdris = await api('/assets?t=hdris'), texs = await api('/assets?t=textures');
for (const [k, w] of Object.entries(WANT.hdris)) {
  try { const id = pick(hdris, w); const f = await api('/files/' + id); const u = f.hdri['1k'].hdr.url;
    manifest.hdris[k] = await dl(u, `hdri_${k}.hdr`); credit(id, hdris[id]); console.log('HDRI', k, id); } catch (e) { console.warn('HDRI', k, e.message); }
}
for (const [k, w] of Object.entries(WANT.textures)) {
  try { const id = pick(texs, w); const f = await api('/files/' + id); const get = re => { const key = Object.keys(f).find(x => re.test(x)); return key && f[key]['1k'] && (f[key]['1k'].jpg || f[key]['1k'].png); };
    const out = {}; const diff = get(/^diff/i), nor = get(/^nor_gl/i), rough = get(/^rough/i);
    if (diff) out.diff = await dl(diff.url, `${k}_diff.jpg`); if (nor) out.nor = await dl(nor.url, `${k}_nor.jpg`); if (rough) out.rough = await dl(rough.url, `${k}_rough.jpg`);
    manifest.textures[k] = out; credit(id, texs[id]); console.log('TEXTURE', k, id, Object.keys(out)); } catch (e) { console.warn('TEXTURE', k, e.message); }
}
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 1));
console.log('OK', JSON.stringify(manifest.credits.map(c => c.id)));
