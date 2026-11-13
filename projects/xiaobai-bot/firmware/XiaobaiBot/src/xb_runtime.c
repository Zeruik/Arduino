/* 小白集成层，Copyright 2026 TechABJ（理工阿白菌）。底层见 vendor/feng/UPSTREAM.json。 */
#include "xb_runtime.h"
#include "feng.h"
#include "feng_tokenizer.h"
#include "xb_utf8.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(ESP_PLATFORM)
#include "esp_heap_caps.h"
static void *alloc(size_t n){return heap_caps_calloc(1,n,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);}
#else
static void *alloc(size_t n){return calloc(1,n);}
#endif
static feng_model_t model;
static feng_tok_t tok;
static feng_kv_t kv;
static feng_workspace_t ws;
static int ready;
static unsigned utf8_rejections,utf8_rollbacks;
unsigned xb_utf8_rejections(void){return utf8_rejections;}
unsigned xb_utf8_rollbacks(void){return utf8_rollbacks;}
int xb_context_tokens(void){return kv.len;}
void xb_reset(void){kv.len=0;}
size_t xb_kv_bytes(void){return feng_kv_bytes(&model,kv.ctx);}
int xb_logits(int token,int pos,float *out,int capacity){
    if(!ready||capacity<(int)model.hdr.vocab)return -1;
    float *p=feng_forward(&model,&kv,&ws,token,pos);if(!p)return -2;
    memcpy(out,p,model.hdr.vocab*sizeof(float));return (int)model.hdr.vocab;
}
int xb_init(const void *mb,size_t mn,const void *tb,size_t tn,int ctx){
    if(ready||ctx<128||ctx>FENG_MAX_SCORES)return -1;
    int rc=feng_model_init(&model,mb,mn);if(rc)return rc;
    if(feng_tok_load(&tok,tb,tn))return -20;
    if(tok.vocab_size!=(int)model.hdr.vocab)return -21;
    kv.ctx=ctx;kv.len=0;
    kv.k_cache=alloc(feng_kv_data_bytes(&model,ctx));kv.v_cache=alloc(feng_kv_data_bytes(&model,ctx));
    size_t ns=feng_kv_scale_slots(&model,ctx);
    kv.k_scale=alloc(ns*2);kv.v_scale=alloc(ns*2);
    int h=(int)model.hdr.hidden, ff=(int)model.hdr.ffn;
    ws.max_ctx=ctx;
    float **slots[]={&ws.x,&ws.xn,&ws.q,&ws.k,&ws.v,&ws.attn,&ws.proj,&ws.gate,&ws.up,&ws.ffn,&ws.logits,&ws.scratch};
    int sizes[]={h,h,h,h,h,h,h,ff,ff,ff,(int)model.hdr.vocab,ctx>ff?ctx:ff};
    for(int i=0;i<12;i++){*slots[i]=alloc(4u*(size_t)sizes[i]);if(!*slots[i])return -22;}
    if(!kv.k_cache||!kv.v_cache||(ns&&(!kv.k_scale||!kv.v_scale)))return -23;
    feng_quant_init();feng_smp_init();ready=1;return 0;
}
int xb_roundtrip(const char *s,char *out,size_t cap,int *ids,int maxids){
    if(!ready||!s||!out||cap<1)return -1;
    int n=feng_tok_encode(&tok,s,ids,maxids);size_t used=0;
    if(n>=maxids)return -2;
    for(int i=0;i<n;i++){char b[128];int z=feng_tok_decode_token(&tok,ids[i],b,sizeof(b));if(z<0||used+(size_t)z>=cap)return -3;memcpy(out+used,b,(size_t)z);used+=(size_t)z;}
    out[used]=0;return n;
}
int xb_answer(const char *q,char *out,size_t cap,int max_new,void (*tick)(void)){
    if(!ready||!q||!out||cap<2)return -1;
    if(strlen(q)>500||feng_tok_has_special(q))return -2;
    if(max_new<1||max_new>192)return -3;
    utf8_rejections=0;utf8_rollbacks=0;
    char prompt[640];int ids[640], hist[192], nh=0;
    snprintf(prompt,sizeof(prompt),"<|im_start|>user\n%s<|im_end|>\n<|im_start|>assistant\n",q);
    int np=feng_tok_encode(&tok,prompt,ids,640);
    if(np>=640||np+max_new+2>kv.ctx)return -4;
    if(kv.len+np+max_new+2>kv.ctx)xb_reset();
    int pos=kv.len;float *logits=NULL;size_t used=0;out[0]=0;
    for(int i=0;i<np;i++){
        logits=feng_forward_ex(&model,&kv,&ws,ids[i],pos++,i==np-1);
        if(!logits){xb_reset();return -5;}if(tick)tick();
    }
    xb_utf8_state utf8={0,0,0};
    size_t complete_used=0;int complete_pos=pos,complete_nh=0;
    for(int i=0;i<max_new;i++){
        int id=feng_sample_greedy(logits,(int)model.hdr.vocab,hist,nh,1.25f,6);
        char b[128];int z=0;xb_utf8_state next=utf8;
        /* Penalties are applied once. Only invalid candidates are then masked;
         * re-running the penalizing sampler here would change valid rankings. */
        for(int attempts=0;id>=0&&attempts<(int)model.hdr.vocab;attempts++){
            int stop=id==tok.id_im_end||id==tok.id_eot;
            next=utf8;z=stop?0:feng_tok_decode_token(&tok,id,b,sizeof(b));
            if((stop&&!utf8.left)||(!stop&&z>0&&xb_utf8_feed(&next,b,(size_t)z)))break;
            logits[id]=-INFINITY;utf8_rejections++;
            id=feng_argmax(logits,(int)model.hdr.vocab);
            if(id<0||!isfinite(logits[id])){id=-1;break;}
        }
        if(id<0||id==tok.id_im_end||id==tok.id_eot)break;
        if(z<0||used+(size_t)z>=cap)break;
        memcpy(out+used,b,(size_t)z);used+=(size_t)z;hist[nh++]=id;
        utf8=next;
        logits=feng_forward(&model,&kv,&ws,id,pos++);
        if(!logits){xb_reset();return -5;}if(tick)tick();
        if(!utf8.left){complete_used=used;complete_pos=pos;complete_nh=nh;}
    }
    /* A budget/cap boundary can cut a byte-token character. Roll back whole
     * token positions too, so displayed text and future KV history agree. */
    if(utf8.left){used=complete_used;pos=complete_pos;nh=complete_nh;utf8_rollbacks++;}
    if(pos<kv.ctx)(void)feng_forward_ex(&model,&kv,&ws,tok.id_im_end,pos++,0);
    int nl=0;if(feng_tok_encode(&tok,"\n",&nl,1)==1&&pos<kv.ctx)(void)feng_forward_ex(&model,&kv,&ws,nl,pos++,0);
    kv.len=pos;
    out[used]=0;return nh;
}
