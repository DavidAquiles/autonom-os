/*
 * KD-15: audio is converted to canonical WAV in the browser. The target is
 * Android only, so MediaRecorder gives us `audio/webm;codecs=opus` and nothing
 * else — we still decode and resample with the standard APIs, because that
 * removes an ffmpeg dependency on the host and leaves the backend exactly one
 * input format to validate.
 *
 * Output, per the contract for POST /api/voice/transcribe:
 *   RIFF PCM, 16-bit little-endian, 16000 Hz, mono.
 */

export const TARGET_RATE = 16000

export async function blobToWav(blob: Blob): Promise<Blob> {
  const bytes = await blob.arrayBuffer()

  const Ctx: typeof AudioContext =
    window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
  const decodeCtx = new Ctx()
  let decoded: AudioBuffer
  try {
    decoded = await decodeCtx.decodeAudioData(bytes.slice(0))
  } finally {
    void decodeCtx.close()
  }

  const frames = Math.max(1, Math.ceil((decoded.duration * TARGET_RATE)))
  const offline = new OfflineAudioContext(1, frames, TARGET_RATE)
  const src = offline.createBufferSource()
  src.buffer = decoded
  src.connect(offline.destination)
  src.start(0)
  const mono = await offline.startRendering()

  return encodeWav(mono.getChannelData(0), TARGET_RATE)
}

export function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample)
  const view = new DataView(buffer)

  writeAscii(view, 0, 'RIFF')
  view.setUint32(4, 36 + samples.length * bytesPerSample, true)
  writeAscii(view, 8, 'WAVE')
  writeAscii(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // PCM chunk size
  view.setUint16(20, 1, true) // PCM
  view.setUint16(22, 1, true) // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * bytesPerSample, true) // byte rate
  view.setUint16(32, bytesPerSample, true) // block align
  view.setUint16(34, 16, true) // bits per sample
  writeAscii(view, 36, 'data')
  view.setUint32(40, samples.length * bytesPerSample, true)

  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

function writeAscii(view: DataView, offset: number, text: string) {
  for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i))
}
