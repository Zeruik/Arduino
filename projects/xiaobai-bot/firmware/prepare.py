Import('env')
from pathlib import Path
root=Path(env['PROJECT_DIR']).parent
page=(root/'web/index.html').read_text()
(root/'firmware/XiaobaiBot/src/xb_page.h').write_text('#pragma once\nstatic const char XB_PAGE[] PROGMEM = R"XBPAGE('+page+')XBPAGE";\n')
env.Append(CFLAGS=['-std=gnu23'])
