import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';

test('publish queues and BLE ACK does not claim delivery; stale ACK is rejected', async () => {
 const dir=await mkdtemp(path.join(os.tmpdir(),'pencilcolour-test-'));
 const port=19000+Math.floor(Math.random()*10000);
 const child=spawn(process.execPath,['index.js'],{cwd:import.meta.dirname,env:{...process.env,DATA_DIR:dir,PORT:String(port),GATEWAY_TOKEN:'test-token'},stdio:'ignore'});
 const base=`http://127.0.0.1:${port}`;
 const request=async (url,method='GET',body)=>fetch(base+url,{method,headers:{Authorization:'Bearer test-token','Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
 try {
  let ready=false;
  for(let i=0;i<100;i++){try{if((await request('/api/state')).ok){ready=true;break}}catch{} await delay(50)}
  assert.ok(ready,'server started');
  let state=await (await request('/api/state')).json();
  const original=state.tags.find(t=>t.id==='ESL-001').published;
  state=await (await request('/api/tags/ESL-001/publish','POST')).json();
  assert.equal(state.tags[0].status,'pending'); assert.deepEqual(state.tags[0].published,original);
  let jobs=(await (await request('/api/gateway/jobs')).json()).jobs;
  let job=jobs.find(j=>j.tagId==='ESL-001'); assert.ok(job);
  assert.equal((await request('/api/gateway/jobs/ESL-001/ack','POST',{jobId:job.id,status:'ble_test'})).status,200);
  state=await (await request('/api/state')).json();
  assert.equal(state.tags[0].status,'pending'); assert.deepEqual(state.tags[0].published,original);
  assert.equal(state.tags[0].bleTest.result,'acknowledged');
  await request('/api/products/p1','PATCH',{price:4.4});
  assert.equal((await request('/api/gateway/jobs/ESL-001/ack','POST',{jobId:job.id,status:'ble_test'})).status,409);
  jobs=(await (await request('/api/gateway/jobs')).json()).jobs;
  assert.notEqual(jobs.find(j=>j.tagId==='ESL-001').id,job.id);
 } finally {child.kill(); await new Promise(resolve=>child.once('exit',resolve)); await rm(dir,{recursive:true,force:true});}
});
