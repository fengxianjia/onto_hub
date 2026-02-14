<template>
  <Dialog v-model="visible" title="Webhook 接入指南" size="lg">
    <div class="space-y-6 overflow-y-auto max-h-[70vh] px-1">
      
      <!-- Intro -->
      <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-sm text-blue-800">
        <p>
          当事件触发时，OntoHub 会向您配置的 URL 发送 <strong>POST</strong> 请求。
          <br>
          如果配置了<strong>签名密钥</strong>，请求头中将包含 <code>X-Hub-Signature-256</code> 用于安全校验。
        </p>
      </div>

      <!-- Payload Structure -->
      <section>
        <h3 class="text-md font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span class="w-1 h-4 bg-primary rounded-full"></span>
          请求 Payload 结构
        </h3>
        
        <div class="space-y-4">
          <!-- Ping Event -->
          <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
            <div class="px-3 py-2 bg-gray-100 border-b border-gray-200 text-xs font-bold text-gray-600 flex justify-between">
              <span>事件: 连通性测试 (ping)</span>
              <span class="font-mono text-gray-400">application/json</span>
            </div>
            <div class="p-3 bg-[#1e1e1e] text-gray-300 text-xs font-mono overflow-x-auto">
<pre>{
  <span class="text-[#9cdcfe">"event"</span>: <span class="text-[#ce9178">"ping"</span>,
  <span class="text-[#9cdcfe">"webhook_id"</span>: <span class="text-[#ce9178">"test-connectivity"</span>,
  <span class="text-[#9cdcfe">"name"</span>: <span class="text-[#ce9178">"Connectivity Test"</span>,
  <span class="text-[#9cdcfe">"timestamp"</span>: <span class="text-[#b5cea8">1715678900.123</span>
}</pre>
            </div>
          </div>

          <!-- Activated Event -->
          <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
            <div class="px-3 py-2 bg-gray-100 border-b border-gray-200 text-xs font-bold text-gray-600 flex justify-between">
              <span>事件: 本体激活 (ontology.activated)</span>
              <span class="font-mono text-gray-400">application/json</span>
            </div>
            <div class="p-3 bg-[#1e1e1e] text-gray-300 text-xs font-mono overflow-x-auto">
<pre>{
  <span class="text-[#9cdcfe">"event"</span>: <span class="text-[#ce9178">"ontology.activated"</span>,
  <span class="text-[#9cdcfe">"id"</span>: <span class="text-[#ce9178">"550e8400-e29b-..."</span>,
  <span class="text-[#9cdcfe">"code"</span>: <span class="text-[#ce9178">"ontology-core"</span>,
  <span class="text-[#9cdcfe">"version"</span>: <span class="text-[#b5cea8">2</span>,
  <span class="text-[#9cdcfe">"name"</span>: <span class="text-[#ce9178">"企业核心本体"</span>,
  <span class="text-[#9cdcfe">"is_active"</span>: <span class="text-[#569cd6">true</span>,
  <span class="text-[#9cdcfe">"timestamp"</span>: <span class="text-[#b5cea8">1715679999.999</span>
}</pre>
            </div>
          </div>
        </div>
      </section>

      <!-- Code Examples -->
      <section>
        <h3 class="text-md font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span class="w-1 h-4 bg-green-500 rounded-full"></span>
          服务端代码示例
        </h3>
        
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div class="flex border-b border-gray-200 bg-gray-50">
            <button 
              v-for="lang in ['Python (FastAPI)', 'Node.js (Express)']" 
              :key="lang"
              @click="currentLang = lang"
              :class="['px-4 py-2 text-xs font-medium transition-colors border-b-2', 
                currentLang === lang ? 'border-primary text-primary bg-white' : 'border-transparent text-gray-500 hover:text-gray-700']"
            >
              {{ lang }}
            </button>
          </div>
          
          <div class="bg-[#1e1e1e] p-4 overflow-x-auto text-xs font-mono text-gray-300 leading-relaxed">
            <template v-if="currentLang === 'Python (FastAPI)'">
<pre><span class="text-[#c586c0">from</span> fastapi <span class="text-[#c586c0">import</span> FastAPI, Request, HTTPException
<span class="text-[#c586c0">import</span> hmac, hashlib, json

app = FastAPI()
SECRET_TOKEN = <span class="text-[#ce9178">"your-secret"</span>

<span class="text-[#569cd6">@app.post</span>(<span class="text-[#ce9178">"/webhook"</span>)
<span class="text-[#569cd6">async def</span> <span class="text-[#dcdcaa">handle_webhook</span>(request: Request):
    <span class="text-[#6a9955"># 1. 获取签名</span>
    signature = request.headers.get(<span class="text-[#ce9178">"X-Hub-Signature-256"</span>)
    
    <span class="text-[#6a9955"># 2. 获取原始数据与 Payload</span>
    content_type = request.headers.get(<span class="text-[#ce9178">"content-type"</span>, <span class="text-[#ce9178">""</span>)
    payload = {}
    
    <span class="text-[#c586c0">if</span> <span class="text-[#ce9178">"multipart/form-data"</span> <span class="text-[#c586c0">in</span> content_type:
        <span class="text-[#6a9955"># 处理文件上传 (例如: 手动推送本体包)</span>
        form = <span class="text-[#c586c0">await</span> request.form()
        payload_str = form.get(<span class="text-[#ce9178">"payload"</span>)
        file = form.get(<span class="text-[#ce9178">"file"</span>) <span class="text-[#6a9955"># UploadFile 对象</span>
        
        <span class="text-[#c586c0">if</span> payload_str:
            payload = json.loads(payload_str)
            
        <span class="text-[#6a9955"># 验证签名 (使用原始 payload 字符串)</span>
        body_to_sign = payload_str.encode() <span class="text-[#c586c0">if</span> payload_str <span class="text-[#c586c0">else</span> b<span class="text-[#ce9178">""</span>
        
        <span class="text-[#c586c0">if</span> file:
            print(<span class="text-[#ce9178">f"Received file: {file.filename}"</span>)
            <span class="text-[#6a9955"># await file.read() # 读取文件内容</span>
            
    <span class="text-[#c586c0">else</span>:
        <span class="text-[#6a9955"># 处理普通 JSON (例如: 自动激活通知)</span>
        body_bytes = <span class="text-[#c586c0">await</span> request.body()
        body_to_sign = body_bytes
        payload = json.loads(body_bytes)

    <span class="text-[#6a9955"># 3. 验证签名</span>
    <span class="text-[#c586c0">if</span> signature:
        expected = <span class="text-[#ce9178">"sha256="</span> + hmac.new(
            SECRET_TOKEN.encode(), body_to_sign, hashlib.sha256
        ).hexdigest()
        <span class="text-[#c586c0">if</span> <span class="text-[#c586c0">not</span> hmac.compare_digest(signature, expected):
            <span class="text-[#c586c0">raise</span> HTTPException(403, <span class="text-[#ce9178">"Invalid signature"</span>)

    <span class="text-[#6a9955"># 4. 处理业务</span>
    event = payload.get(<span class="text-[#ce9178">"event"</span>)
    print(<span class="text-[#ce9178">f"Received event: {event}"</span>)

    <span class="text-[#c586c0">if</span> event == <span class="text-[#ce9178">"ping"</span>:
        <span class="text-[#c586c0">return</span> {<span class="text-[#ce9178">"msg"</span>: <span class="text-[#ce9178">"Pong!"</span>}
    
    <span class="text-[#c586c0">if</span> event == <span class="text-[#ce9178">"ontology.activated"</span>:
        print(<span class="text-[#ce9178">f"Update received: {payload['code']} v{payload['version']}"</span>)
        <span class="text-[#c586c0">return</span> {<span class="text-[#ce9178">"status"</span>: <span class="text-[#ce9178">"processed"</span>}

    <span class="text-[#c586c0">return</span> {<span class="text-[#ce9178">"status"</span>: <span class="text-[#ce9178">"ignored"</span>}</pre>
            </template>

            <template v-else>
<pre><span class="text-[#c586c0">const</span> express = require(<span class="text-[#ce9178">'express'</span>);
<span class="text-[#c586c0">const</span> crypto = require(<span class="text-[#ce9178">'crypto'</span>);
<span class="text-[#c586c0">const</span> app = express();
<span class="text-[#c586c0">const</span> SECRET = <span class="text-[#ce9178">'your-secret'</span>;

<span class="text-[#6a9955">// 保留原始 Body 用于验签</span>
app.use(express.json({ verify: (req, res, buf) => req.rawBody = buf }));

app.post(<span class="text-[#ce9178">'/webhook'</span>, (req, res) => {
  <span class="text-[#c586c0">const</span> signature = req.headers[<span class="text-[#ce9178">'x-hub-signature-256'</span>];
  
  <span class="text-[#6a9955">// 1. 验签</span>
  <span class="text-[#c586c0">if</span> (signature) {
    <span class="text-[#c586c0">const</span> digest = <span class="text-[#ce9178">'sha256='</span> + crypto.createHmac(<span class="text-[#ce9178">'sha256'</span>, SECRET)
      .update(req.rawBody).digest(<span class="text-[#ce9178">'hex'</span>);
    <span class="text-[#c586c0">if</span> (signature !== digest) <span class="text-[#c586c0">return</span> res.status(403).send(<span class="text-[#ce9178">'Invalid signature'</span>);
  }

  <span class="text-[#6a9955">// 2. 业务处理</span>
  <span class="text-[#c586c0">const</span> { event } = req.body;
  <span class="text-[#c586c0">if</span> (event === <span class="text-[#ce9178">'ping'</span>) <span class="text-[#c586c0">return</span> res.json({ msg: <span class="text-[#ce9178">'Pong!'</span> });
  
  console.log(<span class="text-[#ce9178">`Event: ${event}`</span>);
  res.send(<span class="text-[#ce9178">'OK'</span>);
});</pre>
            </template>
          </div>
        </div>
      </section>

    </div>
    
    <template #footer>
      <div class="flex justify-end">
        <Button variant="primary" @click="visible = false">关闭</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Dialog, Button } from './index.js' // Assuming these are exported from index.js

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const currentLang = ref('Python (FastAPI)')
</script>
