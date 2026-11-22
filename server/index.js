import express from 'express';
import cors from 'cors';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const app=express();app.use(cors());app.use(express.json());
const seedFile=new URL('./data/store.json',import.meta.url);
const file=process.env.DATA_DIR?path.join(process.env.DATA_DIR,'store.json'):fileURLToPath(seedFile);
if(process.env.DATA_DIR){await mkdir(process.env.DATA_DIR,{recursive:true});try{await readFile(file,'utf8')}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(file,await readFile(seedFile))}}
let db=JSON.parse(await readFile(file,'utf8'));
let queue=Promise.resolve();
const save=()=>{queue=queue.then(()=>writeFile(file,JSON.stringify(db,null,2)));return queue};
const snapshot=p=>({name:p.name,size:p.size,price:p.price,previousPrice:p.previousPrice,sku:p.sku});
const error=(res,message,code=400)=>res.status(code).json({error:message});
app.get('/api/state',(req,res)=>res.json(db));
app.patch('/api/products/:id',async(req,res)=>{
 const p=db.products.find(x=>x.id===req.params.id);if(!p)return error(res,'Product not found',404);
 const {name,size,price,previousPrice,category}=req.body;
 if(name!==undefined){if(typeof name!=='string'||!name.trim()||name.length>80)return error(res,'Invalid name');p.name=name.trim()}
 if(size!==undefined){if(typeof size!=='string'||size.length>40)return error(res,'Invalid size');p.size=size}
 if(category!==undefined){if(typeof category!=='string'||category.length>40)return error(res,'Invalid category');p.category=category}
 if(price!==undefined){if(typeof price!=='number'||!Number.isFinite(price)||price<0||price>100000)return error(res,'Invalid price');p.price=Math.round(price*100)/100}
 if(previousPrice!==undefined){if(previousPrice!==null&&(typeof previousPrice!=='number'||!Number.isFinite(previousPrice)||previousPrice<0))return error(res,'Invalid previous price');p.previousPrice=previousPrice===null?null:Math.round(previousPrice*100)/100}
 for(const t of db.tags.filter(t=>t.productId===p.id)){if(t.status!=='offline')t.status='pending'}
 db.events.unshift({at:new Date().toISOString(),type:'edit',message:`Edited ${p.sku}`});db.events=db.events.slice(0,50);
 await save();res.json(db);
});
app.post('/api/tags/:id/publish',async(req,res)=>{
 const t=db.tags.find(x=>x.id===req.params.id);if(!t)return error(res,'Tag not found',404);
 const p=db.products.find(x=>x.id===t.productId);if(!p)return error(res,'Assigned product not found',404);
 if(t.status==='offline')return error(res,'Tag offline: cannot publish',409);
 t.status='pending';
 db.events.unshift({at:new Date().toISOString(),type:'publish',message:`Queued ${p.sku} for ${t.id}`});db.events=db.events.slice(0,50);
 await save();res.json(db);
});
app.post('/api/tags/:id/connectivity',async(req,res)=>{
 const t=db.tags.find(x=>x.id===req.params.id);if(!t)return error(res,'Tag not found',404);
 if(typeof req.body.offline!=='boolean')return error(res,'offline must be boolean');
 t.status=req.body.offline?'offline':'pending';await save();res.json(db);
});
app.post('/api/tags/:id/assign',async(req,res)=>{
 const t=db.tags.find(x=>x.id===req.params.id);if(!t)return error(res,'Tag not found',404);
 if(!db.products.some(p=>p.id===req.body.productId))return error(res,'Product not found',404);
 t.productId=req.body.productId;t.status=t.status==='offline'?'offline':'pending';await save();res.json(db);
});
// Prototype gateway integration. Requires GATEWAY_TOKEN; not a production auth system.
const gatewayToken=process.env.GATEWAY_TOKEN;
const gatewayJobs=new Map();
const gatewayAuth=(req,res,next)=>{
 if(!gatewayToken)return error(res,'Gateway integration disabled: set GATEWAY_TOKEN',503);
 if(req.get('Authorization')!==`Bearer ${gatewayToken}`)return error(res,'Unauthorized gateway',401);
 next();
};
app.get('/api/gateway/jobs',gatewayAuth,(req,res)=>{
 const jobs=[];
 for(const t of db.tags.filter(t=>t.status==='pending')){
  const p=db.products.find(x=>x.id===t.productId);
  if(!p)continue;
  const version=JSON.stringify(snapshot(p));
  const job={id:`${t.id}:${createHash('sha256').update(version).digest('base64url')}`,tagId:t.id,product:snapshot(p),version};
  gatewayJobs.set(t.id,{...job,state:'pending'});jobs.push({id:job.id,tagId:job.tagId,product:job.product});
 }
 res.json({jobs});
});
app.post('/api/gateway/jobs/:tagId/ack',gatewayAuth,async(req,res)=>{
 const job=gatewayJobs.get(req.params.tagId);
 if(!job||job.id!==req.body.jobId)return error(res,'Unknown or stale job',409);
 if(!['delivered','failed','ble_test'].includes(req.body.status))return error(res,'Invalid status');
 const tag=db.tags.find(t=>t.id===req.params.tagId);
 if(!tag)return error(res,'Tag not found',404);
 const product=db.products.find(p=>p.id===tag.productId);
 if(tag.status!=='pending'||!product||JSON.stringify(snapshot(product))!==job.version)return error(res,'Unknown or stale job',409);
 if(req.body.status==='ble_test'){
  tag.bleTest={jobId:job.id,at:new Date().toISOString(),result:'acknowledged'};
 }else if(req.body.status==='delivered'){
  tag.published=job.product;tag.status='synced';tag.updatedAt=new Date().toISOString();
  job.state='delivered';
 }else{tag.status='pending';job.state='failed'}
 db.events.unshift({at:new Date().toISOString(),type:'gateway',message:`Gateway reported ${req.body.status} for ${tag.id}`});
 db.events=db.events.slice(0,50);await save();res.json({ok:true});
});
const dist=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../client/dist');
app.use(express.static(dist));
app.get(/^(?!\/api\/).*/, (req,res)=>res.sendFile(path.join(dist,'index.html')));
const port=Number(process.env.PORT)||3001;
app.listen(port,'0.0.0.0',()=>console.log(`PencilColour listening on ${port}`));
