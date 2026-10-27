// verify-ids.mjs — بوّابة البناء: تتأكّد أنّ كل معرّف عنصر (box id) نُقل إلى الـ GLB
// (باسم العقدة أو extras.elementId). تفشل إن ضاع أيّ معرّف — أهمّ حماية للربط بالسجل.
// تقرأ حتى ملفات meshopt المضغوطة. الاستخدام:
//   node verify-ids.mjs <site_scene.json> <prefix|""> <glb1> [glb2 ...]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import { readFileSync } from 'node:fs';

const [, , scenePath, prefixArg, ...glbs] = process.argv;
const prefix = prefixArg === '""' ? '' : (prefixArg || '');
if (!scenePath || glbs.length === 0) {
  console.error('usage: node verify-ids.mjs <site_scene.json> <prefix|""> <glb1> [glb2 ...]');
  process.exit(2);
}

await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.decoder': MeshoptDecoder });

const present = new Set();
let totalNodes = 0;
for (const g of glbs) {
  const doc = await io.read(g);
  const nodes = doc.getRoot().listNodes();
  totalNodes += nodes.length;
  for (const n of nodes) {
    const nm = n.getName();
    if (nm) present.add(nm);
    const ex = n.getExtras() || {};
    if (ex.elementId) present.add(String(ex.elementId));
  }
}

const scene = JSON.parse(readFileSync(scenePath, 'utf8'));
const expected = scene.boxes
  .filter((b) => b.type !== 'label' && (!prefix || prefix.split(',').some((p) => String(b.id).startsWith(p))))
  .map((b) => b.id);

const missing = expected.filter((id) => !present.has(id));
console.log(JSON.stringify({
  prefix: prefix || '(all)',
  glbs: glbs.length,
  nodesInGlb: totalNodes,
  distinctIdsPresent: present.size,
  expectedBoxIds: expected.length,
  missing: missing.length,
}, null, 0));

if (missing.length) {
  console.error('GATE FAILED — missing ids (first 40):', missing.slice(0, 40));
  process.exit(1);
}
console.log('GATE OK — every exported box id survived into the GLB(s).');
