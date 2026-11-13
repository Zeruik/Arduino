#include "xb_utf8.h"
int probe(xb_utf8_state *s,const char*b,size_t n){return xb_utf8_feed(s,b,n);}
