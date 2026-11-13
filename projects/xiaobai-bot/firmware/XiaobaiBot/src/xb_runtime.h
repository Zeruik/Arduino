#ifndef XB_RUNTIME_H
#define XB_RUNTIME_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
int xb_init(const void *model,size_t msize,const void *tokens,size_t tsize,int ctx);
int xb_answer(const char *question,char *answer,size_t capacity,int max_new,void (*tick)(void));
int xb_roundtrip(const char *text,char *out,size_t capacity,int *ids,int maxids);
size_t xb_kv_bytes(void);
void xb_reset(void);
int xb_logits(int token,int pos,float *out,int capacity);
unsigned xb_utf8_rejections(void);
unsigned xb_utf8_rollbacks(void);
int xb_context_tokens(void);
#ifdef __cplusplus
}
#endif
#endif
