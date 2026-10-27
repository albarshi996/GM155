// fetch-polyhaven.mjs — ينزّل خامات Poly Haven CC0 عبر الـ API الحرّ (بلا إضافة مدفوعة).
// يجرّب عدّة slugs لكل دور ويأخذ أوّل المتاح. يحفظ باسم الدور لتبسيط الربط في Blender.
// الاستخدام: node fetch-polyhaven.mjs
import { mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const UA = { 'User-Agent': 'GM155-realism/1.0 (albarshi.96@gmail.com)' };
const RES = '1k';
const TIMEOUT = 45000;
function withTimeout(url, opts = {}) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), TIMEOUT);
  return fetch(url, { ...opts, signal: ac.signal }).finally(() => clearTimeout(t));
}
const HERE = dirname(fileURLToPath(import.meta.url));
const TEX = resolve(HERE, '..', 'assets', 'textures');
const HDR = resolve(HERE, '..', 'assets', 'hdri');
await mkdir(TEX, { recursive: true }); await mkdir(HDR, { recursive: true });

const ROLES = {
  floor:     { type: 'textures', cands: ['concrete_floor_02', 'hangar_concrete_floor', 'rough_concrete', 'concrete_floor_worn_001'] },
  wall:      { type: 'textures', cands: ['concrete_wall_005', 'concrete_wall_008', 'painted_concrete', 'concrete_wall_006'] },
  rackmetal: { type: 'textures', cands: ['metal_plate', 'sheet_metal_02', 'metal_plate_02', 'painted_metal_02'] },
  roofmetal: { type: 'textures', cands: ['box_profile_metal_sheet', 'corrugated_iron', 'metal_roof_02', 'metal_sheet'] },
  asphalt:   { type: 'textures', cands: ['clean_asphalt', 'asphalt_02', 'rough_asphalt', 'asphalt_road'] },
  hdri:      { type: 'hdris',    cands: ['kloofendal_48d_partly_cloudy_puresky', 'qwantani_noon_puresky', 'kloppenheim_06_puresky', 'syferfontein_0d_clear_puresky'] },
};

async function getJson(url) {
  const r = await withTimeout(url, { headers: UA });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  return r.json();
}
async function download(url, out) {
  const r = await withTimeout(url, { headers: UA });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
  await writeFile(out, Buffer.from(await r.arrayBuffer()));
  return (await import('node:fs')).statSync(out).size;
}
function pick(obj, res, prefFmts) {
  const lvl = obj && obj[res]; if (!lvl) return null;
  for (const f of prefFmts) if (lvl[f] && lvl[f].url) return { url: lvl[f].url, ext: f };
  const k = Object.keys(lvl)[0]; return lvl[k] && lvl[k].url ? { url: lvl[k].url, ext: k } : null;
}

const report = {};
for (const [role, def] of Object.entries(ROLES)) {
  let done = false;
  for (const slug of def.cands) {
    try {
      const files = await getJson('https://api.polyhaven.com/files/' + slug);
      if (def.type === 'hdris') {
        const h = pick(files.hdri, RES, ['hdr', 'exr']);
        if (!h) continue;
        const out = resolve(HDR, role + '.' + (h.ext === 'exr' ? 'exr' : 'hdr'));
        const sz = await download(h.url, out);
        report[role] = { slug, saved: out.split(/[\\/]/).pop(), bytes: sz }; done = true; break;
      } else {
        const maps = { Diffuse: ['jpg', 'png'], arm: ['jpg', 'png'], nor_gl: ['png', 'jpg', 'exr'] };
        const got = {};
        for (const [mapName, fmts] of Object.entries(maps)) {
          const src = files[mapName] || files[mapName === 'Diffuse' ? 'Color' : mapName];
          const p = pick(src, RES, fmts);
          if (!p) continue;
          const out = resolve(TEX, role + '_' + mapName + '.' + p.ext);
          got[mapName] = { file: out.split(/[\\/]/).pop(), bytes: await download(p.url, out) };
        }
        if (Object.keys(got).length) { report[role] = { slug, maps: got }; done = true; break; }
      }
    } catch (e) { /* try next candidate */ }
  }
  if (!done) report[role] = { ERROR: 'no candidate resolved', tried: def.cands };
}
console.log(JSON.stringify(report, null, 1));
