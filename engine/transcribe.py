import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
for p in sys.argv[1:]:
    a = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True).stdout, np.float32)
    segs,_ = m.transcribe(a, language='es', word_timestamps=True)
    W = [[w.word.strip(), round(w.start,2), round(w.end,2)] for s in segs for w in s.words]
    json.dump(W, open(p.replace('.mp3','.words.json'),'w'), ensure_ascii=False)
    print(p, len(W), round(len(a)/16000,2), 'last', W[-1])
    print(' '.join(w[0] for w in W))
