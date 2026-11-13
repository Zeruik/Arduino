#ifndef XB_UTF8_H
#define XB_UTF8_H
#include <stddef.h>
/* RFC 3629 prefix state. NUL is disallowed by the string-based chat API. */
typedef struct { unsigned char left, lo, hi; } xb_utf8_state;
static inline int xb_utf8_feed(xb_utf8_state *state, const char *bytes, size_t n){
    xb_utf8_state s=*state;
    for(size_t i=0;i<n;i++){
        unsigned char b=(unsigned char)bytes[i];
        if(s.left){
            if(b<s.lo||b>s.hi)return 0;
            s.left--;s.lo=0x80;s.hi=0xbf;
        }else if(b==0)return 0;
        else if(b<0x80)continue;
        else if(b>=0xc2&&b<=0xdf){s.left=1;s.lo=0x80;s.hi=0xbf;}
        else if(b>=0xe0&&b<=0xef){s.left=2;s.lo=b==0xe0?0xa0:0x80;s.hi=b==0xed?0x9f:0xbf;}
        else if(b>=0xf0&&b<=0xf4){s.left=3;s.lo=b==0xf0?0x90:0x80;s.hi=b==0xf4?0x8f:0xbf;}
        else return 0;
    }
    *state=s;return 1;
}
#endif
