import ctypes as C,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Native:
    def __init__(self,model_dir,ctx=512,fp32_kv=False,library_path=None):
        path=ROOT/'build'/(('xiaobai-f32.dll' if os.name=='nt' else 'libxiaobai-f32.so') if fp32_kv else ('xiaobai.dll' if os.name=='nt' else 'libxiaobai.so'))
        self.lib=C.CDLL(str(library_path or path));lib=self.lib
        lib.xb_init.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_int]
        lib.xb_answer.argtypes=[C.c_char_p,C.c_void_p,C.c_size_t,C.c_int,C.c_void_p]
        lib.xb_roundtrip.argtypes=[C.c_char_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_int]
        lib.xb_kv_bytes.restype=C.c_size_t
        d=Path(model_dir);self.mb=C.create_string_buffer((d/'model.bin').read_bytes());self.tb=C.create_string_buffer((d/'tokenizer.bin').read_bytes())
        rc=lib.xb_init(self.mb,len(self.mb)-1,self.tb,len(self.tb)-1,ctx)
        if rc:raise RuntimeError(f'模型初始化失败 {rc}')
    def answer(self,q,n=96,reset=True):
        if reset:self.lib.xb_reset()
        b=C.create_string_buffer(4096);rc=self.lib.xb_answer(q.encode(),b,len(b),n,None)
        if rc<0:raise ValueError(f'输入或推理错误 {rc}')
        return b.value.decode('utf-8')
    def tokens(self,s):
        out=C.create_string_buffer(65536);ids=(C.c_int*32768)()
        n=self.lib.xb_roundtrip(s.encode(),out,len(out),ids,len(ids))
        if n<0:raise ValueError(n)
        return list(ids[:n]),out.value.decode('utf-8')
