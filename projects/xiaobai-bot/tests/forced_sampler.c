/* Test-only symbol interposition. Not linked into the firmware/host library. */
static int token;
void force_token(int id){token=id;}
int feng_sample_greedy(float *l,int n,const int*h,int nh,float p,int nr){(void)l;(void)n;(void)h;(void)nh;(void)p;(void)nr;return token;}
