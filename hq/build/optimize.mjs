// optimize.mjs — خطّ تحسين GLB «آمن للأسماء» فقط: dedup + weld + prune + meshopt.
// يُمنع صراحةً: instance / join / flatten / simplify / palette (تحذف هويّة العناصر).
// يُثبّت extras.elementId = اسم العقدة قبل أي عملية. الاستخدام: node optimize.mjs <in.glb> <out.glb>
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, weld, prune, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import { statSync } from 'node:fs';

const [, , inPath, outPath] = process.argv;
if (!inPath || !outPath) { console.error('usage: node optimize.mjs <in.glb> <out.glb>'); process.exit(2); }

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });

const doc = await io.read(inPath);
// belt-and-suspenders: guarantee extras.elementId on every node (fallback to its name)
for (const n of doc.getRoot().listNodes()) {
  const nm = n.getName();
  const ex = n.getExtras() || {};
  if (nm && !ex.elementId) { ex.elementId = nm; n.setExtras(ex); }
}

await doc.transform(
  dedup(),
  weld(),
  prune({ keepLeaves: true, keepExtras: true }),
  meshopt({ encoder: MeshoptEncoder, level: 'high' }),
);

await io.write(outPath, doc);
const bIn = statSync(inPath).size, bOut = statSync(outPath).size;
console.log(JSON.stringify({ in: inPath.split(/[\\/]/).pop(), out: outPath.split(/[\\/]/).pop(), bytesIn: bIn, bytesOut: bOut, ratio: +(bOut / bIn).toFixed(3) }));
