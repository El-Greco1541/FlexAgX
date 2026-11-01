/** Zero-dependency JavaScript glue client for the staged FlexAgX API.
 * Node.js 18+ (Buffer/fetch); not a GPU adapter or ReShade runtime plugin.
 */
import { readFile, writeFile } from 'node:fs/promises';

export async function processFrame({
  api = 'http://127.0.0.1:8080',
  imagePath,
  outputPath,
  sessionId = 'javascript-client',
  frameIndex = 0,
  dtMs = 16.667,
  settings = {},
}) {
  const image = await readFile(imagePath);
  const response = await fetch(`${api}/v1/frame`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      frame_index: frameIndex,
      dt_ms: dtMs,
      image_png_base64: image.toString('base64'),
      settings,
    }),
  });
  if (!response.ok) {
    throw new Error(`FlexAgX API ${response.status}: ${await response.text()}`);
  }
  const result = await response.json();
  if (outputPath) await writeFile(outputPath, Buffer.from(result.image_png_base64, 'base64'));
  return result;
}

if (process.argv[1]?.endsWith('flexagx_client.mjs') && process.argv.length >= 4) {
  processFrame({ imagePath: process.argv[2], outputPath: process.argv[3] })
    .then(r => console.log(JSON.stringify({ width: r.width, height: r.height, mode: r.mode,
      tone_validation: r.tone_validation }, null, 2)))
    .catch(e => { console.error(e.message); process.exitCode = 1; });
}
