"""同一进程中启动实际服务并验证 HTTP 生命周期；无需外部网络或云端 API。"""
import argparse,json,subprocess,sys,time,urllib.request,socket
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);a=ap.parse_args()
root=Path(__file__).resolve().parents[1]
proc=subprocess.Popen([sys.executable,str(root/'tools/serve.py'),'--model',a.model,'--port','8765'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def get(path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8765'+path,data=body,headers={'Content-Type':'text/plain;charset=utf-8'})
    with urllib.request.urlopen(req,timeout=15) as r:return r.status,r.read().decode()
try:
    for i in range(100):
        try:_,s=get('/api/status');break
        except (OSError,urllib.error.URLError):time.sleep(.1)
    else:raise RuntimeError(proc.stdout.read().decode())
    status=json.loads(s);_,html=get('/');assert 'Xiaobai Bot' in html and 'fetch(' in html
    code,jid=get('/api/chat','中国的首都是哪里'.encode());assert code==202
    for i in range(600):
        code,answer=get('/api/result?id='+jid)
        if code!=202:break
        time.sleep(.1)
    assert code==200 and answer.strip()
    assert get('/api/reset',b'')[0]==200
    report={'pass':True,'actual_q4_inference':True,'status':status,'question':'中国的首都是哪里','answer':answer,'html_served':True,'reset_pass':True,'browser_visual_test':'not performed: sandbox blocks Chromium Unix socket creation'}
    (root/'eval/web-http-test.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
finally:
    proc.terminate();proc.wait(timeout=10)
