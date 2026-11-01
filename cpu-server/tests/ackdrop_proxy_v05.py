"""Local-only fault proxy: make finalize succeed, then discard its HTTP acknowledgment."""
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response
app=FastAPI()
URL=os.environ['ACKDROP_TARGET_CONTROLLER']
seen=0
@app.api_route('/{path:path}', methods=['GET','POST','DELETE'])
async def forward(path:str,request:Request):
    global seen
    async with httpx.AsyncClient(timeout=10) as client:
        r=await client.request(request.method,URL+'/'+path,content=await request.body(),headers={'content-type':'application/json'})
    if path=='v1/control/finalize' and r.status_code==200 and seen==0:
        seen+=1
        return Response(content='lost-ack-test',status_code=504)
    return Response(content=r.content,status_code=r.status_code,media_type=r.headers.get('content-type','application/json'))
