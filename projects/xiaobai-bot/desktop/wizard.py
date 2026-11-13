"""Windows 安装向导：本地选目录、检查包哈希、选择型号与串口后烧录。"""
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
import json,hashlib,shutil,subprocess,threading,sys,os
import serial.tools.list_ports

class Wizard:
    def __init__(self):
        self.root=tk.Tk();self.root.title('小白Bot · Xiaobai Bot 安装向导');self.root.geometry('660x500')
        self.step=0;self.folder=tk.StringVar(value=str(Path.home()/'XiaobaiBot'));self.pack=tk.StringVar();self.agree=tk.BooleanVar();self.port=tk.StringVar();self.profile=tk.StringVar(value='N16R8');self.working=False
        self.body=ttk.Frame(self.root,padding=24);self.body.pack(fill='both',expand=True)
        self.nav=ttk.Frame(self.root,padding=16);self.nav.pack(fill='x');self.back=ttk.Button(self.nav,text='上一步',command=self.prev);self.back.pack(side='left');self.next=ttk.Button(self.nav,text='下一步',command=self.advance);self.next.pack(side='right');self.draw()
    def draw(self):
        for w in self.body.winfo_children():w.destroy()
        self.back['state']='normal' if self.step>0 and not self.working else 'disabled'
        self.next['text']='烧录到开发板' if self.step==3 else '下一步'
        ttk.Label(self.body,text=['欢迎安装小白Bot','选择安装位置','导入模型与固件包','连接开发板'][self.step],font=('',18)).pack(anchor='w',pady=(0,20))
        if self.step==0:
            ttk.Label(self.body,text='理工阿白菌 / TechABJ\n中文本地极轻量语言模型\n\n基于 feng-30m 开源底座继续训练。\n代码与底座许可：Apache-2.0。\n完整许可与第三方声明见安装目录。\n\n部署后使用串口或芯片热点网页对话，无需云端 API。\n候选版能力有限，请查看验证报告。',wraplength=580).pack(anchor='w')
            ttk.Checkbutton(self.body,text='我已阅读 Apache-2.0 许可与第三方声明',variable=self.agree).pack(anchor='w',pady=20)
        elif self.step==1:
            ttk.Entry(self.body,textvariable=self.folder,width=65).pack(fill='x');ttk.Button(self.body,text='浏览…',command=lambda:self.folder.set(filedialog.askdirectory() or self.folder.get())).pack(anchor='w',pady=12)
        elif self.step==2:
            ttk.Label(self.body,text='选择已解压交付包中的 manifest.json。\n向导会校验 SHA-256，不会从任意网址下载或执行程序。').pack(anchor='w')
            ttk.Entry(self.body,textvariable=self.pack,width=65).pack(fill='x',pady=12);ttk.Button(self.body,text='选择交付包…',command=lambda:self.pack.set(filedialog.askopenfilename(filetypes=[('Manifest','manifest.json')]) or self.pack.get())).pack(anchor='w')
        else:
            ttk.Label(self.body,text='型号必须与板上标记一致。烧录会覆盖应用和模型分区；\n请先备份板上的原程序。USB 线需要支持数据传输。').pack(anchor='w')
            ttk.Combobox(self.body,textvariable=self.profile,values=['N16R8','N32R16'],state='readonly').pack(anchor='w',pady=10)
            ttk.Combobox(self.body,textvariable=self.port,values=[p.device for p in serial.tools.list_ports.comports()]).pack(anchor='w')
            self.log=tk.Text(self.body,height=12,width=75);self.log.pack(pady=12)
    def prev(self):
        if not self.working:self.step=max(0,self.step-1);self.draw()
    def advance(self):
        if self.working:return
        if self.step==0 and not self.agree.get():messagebox.showinfo('许可','请先阅读并同意许可。');return
        if self.step==1:
            try:Path(self.folder.get()).mkdir(parents=True,exist_ok=True)
            except OSError as e:messagebox.showerror('目录错误',str(e));return
        if self.step==2:
            try:
                p=Path(self.pack.get()).resolve();m=json.loads(p.read_text());base=p.parent
                dest=Path(self.folder.get())/'packages'/m['profile'];dest.mkdir(parents=True,exist_ok=True)
                for f in m['files']:
                    src=(base/f['name']).resolve()
                    if not src.is_relative_to(base):raise ValueError('交付包路径越界')
                    if hashlib.sha256(src.read_bytes()).hexdigest()!=f['sha256']:raise ValueError('文件校验失败：'+f['name'])
                    target=dest/f['name'];target.parent.mkdir(parents=True,exist_ok=True)
                    if src!=target.resolve():shutil.copy2(src,target)
                shutil.copy2(p,dest/'manifest.json');self.installed=dest;self.manifest=m
                self.profile.set(m['profile'])
            except Exception as e:messagebox.showerror('交付包错误',str(e));return
        if self.step<3:self.step+=1;self.draw();return
        if self.profile.get()!=self.manifest['profile']:messagebox.showerror('型号错误','所选型号与交付包不一致。');return
        if not self.port.get():messagebox.showinfo('串口','请选择开发板串口。');return
        if not messagebox.askyesno('确认烧录','将覆盖所选开发板的应用和模型分区。现在开始？'):return
        self.working=True;self.next['state']='disabled';self.back['state']='disabled';threading.Thread(target=self.flash,daemon=True).start()
    def append(self,s):self.log.insert('end',s);self.log.see('end')
    def flash(self):
        try:
            # 冻结版同时提供 esptool.exe；源码版使用当前 Python 模块。
            exe=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'esptool.exe'
            cmd=[str(exe)] if getattr(sys,'frozen',False) else [sys.executable,'-m','esptool']
            if getattr(sys,'frozen',False) and not exe.exists():raise FileNotFoundError('交付包缺少 esptool.exe')
            cmd+=['--chip','esp32s3','--port',self.port.get(),'--baud','460800','write-flash','--flash-size','16MB' if self.profile.get()=='N16R8' else '32MB']
            for f in self.manifest['files']:
                if 'offset' in f:cmd += [hex(f['offset']),str(self.installed/f['name'])]
            proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in proc.stdout:self.root.after(0,self.append,line)
            if proc.wait():raise RuntimeError('烧录工具返回非零状态，请查看日志。')
            self.root.after(0,messagebox.showinfo,'完成','烧录完成。连接 XiaobaiBot 热点，密码 xiaobai2026，打开 http://192.168.4.1。')
        except Exception as e:self.root.after(0,messagebox.showerror,'未完成',str(e))
        finally:
            self.working=False;self.root.after(0,lambda:self.next.configure(state='normal'))

if __name__=='__main__':Wizard().root.mainloop()
