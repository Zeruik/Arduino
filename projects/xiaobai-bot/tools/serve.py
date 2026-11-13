"""本地验证服务，真实调用和板端相同的 Q4 C 核心；无预设问答。"""
import argparse,json,threading,time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from native import Native, ROOT
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--port',type=int,default=8765);ap.add_argument('--ctx',type=int)
a=ap.parse_args()
if a.ctx is None:a.ctx=int(json.loads((Path(a.model)/'export_info.json').read_text()).get('ctx',512))
engine=Native(a.model,a.ctx);lock=threading.Lock();job={'id':0,'busy':False,'answer':'','error':False}
def run(q):
    try:ans=engine.answer(q,96,reset=False);err=False
    except Exception as e:ans=str(e);err=True
    with lock:job.update(answer=ans,error=err,busy=False)
class Handler(BaseHTTPRequestHandler):
    def send(self,status,text,kind='text/plain;charset=utf-8'):
        b=text.encode();self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        path=urlparse(self.path)
        if path.path=='/':return self.send(200,(ROOT/'web/index.html').read_text(),'text/html;charset=utf-8')
        if path.path=='/api/status':return self.send(200,json.dumps({'mode':'电脑验证 · 实际 Q4 推理','profile':Path(a.model).name,'ctx':a.ctx,'kv_bytes':engine.lib.xb_kv_bytes(),'busy':job['busy']},ensure_ascii=False),'application/json')
        if path.path=='/api/result':
            with lock:
                if parse_qs(path.query).get('id',[''])[0]!=str(job['id']):return self.send(404,'任务不存在')
                return self.send(202 if job['busy'] else 500 if job['error'] else 200,job['answer'])
        self.send(404,'Not found')
    def do_POST(self):
        if self.path=='/api/reset':
            with lock:
                if job['busy']:return self.send(409,'模型正在运行')
                engine.lib.xb_reset();return self.send(200,'OK')
        if self.path!='/api/chat':return self.send(404,'Not found')
        try:n=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.send(400,'Invalid length')
        if n<1 or n>500:return self.send(413,'请使用较短问题，最多 500 UTF-8 字节')
        try:q=self.rfile.read(n).decode('utf-8')
        except UnicodeError:return self.send(400,'Invalid UTF-8')
        with lock:
            if job['busy']:return self.send(409,'模型正在运行')
            job.update(id=job['id']+1,busy=True,answer='',error=False);jid=job['id']
        threading.Thread(target=run,args=(q,),daemon=True).start();self.send(202,str(jid))
print(f'http://127.0.0.1:{a.port} · actual Q4 engine',flush=True)
ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
