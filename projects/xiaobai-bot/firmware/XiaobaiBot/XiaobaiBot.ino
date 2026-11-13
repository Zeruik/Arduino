/* 小白Bot / Xiaobai Bot — Copyright 2026 TechABJ（理工阿白菌），Apache-2.0。
 * 同一份 Q4 C23 引擎用于主机验证和 ESP32。模型从 Flash mmap 读取，无 SD、无聊天 API。
 */
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <esp_partition.h>
#include <esp_heap_caps.h>
#include "src/xb_runtime.h"
#include "src/xb_page.h"
#ifndef XB_CTX
#define XB_CTX 512
#endif
#ifndef XB_PROFILE
#define XB_PROFILE 16
#endif
WebServer server(80);
static SemaphoreHandle_t mutex;
static bool busy=false,failed=false,ready=false;
static unsigned jobId=0;
static char question[512],answer[4096];
static bool serialJob=false;
static TaskHandle_t workerHandle=nullptr;
static void tick(){vTaskDelay(1);}
static void worker(void*){
  for(;;){ulTaskNotifyTake(pdTRUE,portMAX_DELAY);
    int rc=xb_answer(question,answer,sizeof(answer),96,tick);
    xSemaphoreTake(mutex,portMAX_DELAY);
    failed=rc<0;if(failed)snprintf(answer,sizeof(answer),"推理失败，错误码 %d；请缩短问题。",rc);
    if(serialJob){Serial.print("小白> ");Serial.println(answer);Serial.println("> ");}
    busy=false;xSemaphoreGive(mutex);
  }
}
static bool submit(const String &q,bool serial){
  if(q.length()==0||q.length()>500)return false;
  xSemaphoreTake(mutex,portMAX_DELAY);
  if(busy||!ready){xSemaphoreGive(mutex);return false;}
  q.toCharArray(question,sizeof(question));answer[0]=0;failed=false;busy=true;serialJob=serial;jobId++;
  xSemaphoreGive(mutex);xTaskNotifyGive(workerHandle);return true;
}
static bool initModel(){
  if(!psramFound()||ESP.getPsramSize()<8*1024*1024)return false;
  const esp_partition_t *mp=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,ESP_PARTITION_SUBTYPE_ANY,"model");
  const esp_partition_t *tp=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,ESP_PARTITION_SUBTYPE_ANY,"tokdata");
  if(!mp||!tp)return false;
  const void *mb=nullptr;esp_partition_mmap_handle_t handle;
  if(esp_partition_mmap(mp,0,mp->size,ESP_PARTITION_MMAP_DATA,&mb,&handle)!=ESP_OK)return false;
  void *tb=heap_caps_malloc(tp->size,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);if(!tb)return false;
  if(esp_partition_read(tp,0,tb,tp->size)!=ESP_OK){free(tb);return false;}
  int rc=xb_init(mb,mp->size,tb,tp->size,XB_CTX);free(tb);
  Serial.printf("模型初始化 rc=%d，KV=%u B，PSRAM 剩余=%u B\n",rc,(unsigned)xb_kv_bytes(),ESP.getFreePsram());return rc==0;
}
void setup(){
  Serial.begin(115200);delay(800);Serial.println("小白Bot / Xiaobai Bot · TechABJ / 理工阿白菌");
  mutex=xSemaphoreCreateMutex();if(!mutex){Serial.println("互斥量分配失败");return;}
  ready=initModel();
  if(ready&&xTaskCreatePinnedToCore(worker,"xiaobai",16384,nullptr,1,&workerHandle,1)!=pdPASS){ready=false;Serial.println("推理任务分配失败");}
  WiFi.mode(WIFI_AP);WiFi.softAP("XiaobaiBot","xiaobai2026");
  server.on("/",HTTP_GET,[]{server.send_P(200,"text/html;charset=utf-8",XB_PAGE);});
  server.on("/api/status",HTTP_GET,[]{String s="{\"mode\":\"ESP32-S3 板端 · 离线\",\"profile\":\"N"+String(XB_PROFILE)+"\",\"ready\":"+(ready?"true":"false")+",\"ctx\":"+String(XB_CTX)+",\"psram_free\":"+String(ESP.getFreePsram())+"}";server.send(200,"application/json",s);});
  server.on("/api/chat",HTTP_POST,[]{String q=server.arg("plain");if(q.length()>500){server.send(413,"text/plain","问题过长");return;}if(!submit(q,false)){server.send(409,"text/plain;charset=utf-8",ready?"正在生成，请稍候":"模型未就绪，请检查串口和模型分区");return;}server.send(202,"text/plain",String(jobId));});
  server.on("/api/result",HTTP_GET,[]{xSemaphoreTake(mutex,portMAX_DELAY);if(server.arg("id")!=String(jobId))server.send(404,"text/plain","任务不存在");else server.send(busy?202:failed?500:200,"text/plain;charset=utf-8",answer);xSemaphoreGive(mutex);});
  server.on("/api/reset",HTTP_POST,[]{xSemaphoreTake(mutex,portMAX_DELAY);if(busy)server.send(409,"text/plain","busy");else {xb_reset();server.send(200,"text/plain","OK");}xSemaphoreGive(mutex);});
  server.begin();Serial.print("热点 XiaobaiBot / xiaobai2026，网页 http://");Serial.println(WiFi.softAPIP());
  Serial.println(ready?"模型已加载；输入问题后回车。":"模型未加载；请检查分区、PSRAM和权重。");
}
void loop(){
  server.handleClient();static String line;
  while(Serial.available()){
    char c=Serial.read();if(c=='\r')continue;
    if(c=='\n'){if(line=="/reset"){xSemaphoreTake(mutex,portMAX_DELAY);if(!busy)xb_reset();xSemaphoreGive(mutex);}else if(!submit(line,true))Serial.println("未提交：模型未就绪、忙碌或输入过长。");line="";}
    else if(line.length()<501)line+=c;
  }
  delay(2);
}
