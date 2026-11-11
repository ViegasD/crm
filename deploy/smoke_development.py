"""Run on the VPS with a private credentials JSON path; never logs credentials."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys


def container(service):
    return subprocess.check_output([
        "docker", "ps", "-q", "--filter", "label=com.docker.compose.project=hermes_crm2-dev",
        "--filter", "label=com.docker.compose.service=" + service,
    ], text=True).strip()


def run_inside(service, code, data=None):
    result = subprocess.run(["docker", "exec", "-i", container(service), "python", "-c", code],
                            input=json.dumps(data) if data else "", text=True,
                            capture_output=True, timeout=120)
    if result.returncode:
        # Secrets could occur in SQL/config exceptions: retain raw errors privately.
        Path("/srv/crm2/ops/smoke-error.log").write_text(result.stderr)
        raise RuntimeError("Container check failed; inspect private smoke-error.log")
    return result.stdout


def main():
    credentials = json.loads(Path(sys.argv[1]).read_text())
    checks = []
    code = r'''
import asyncio,json,sys,httpx
from urllib.parse import urljoin, urlsplit
import websockets
from app.core.minio import delete_object
from app.workers.celery_app import celery_app

async def main(values):
    checks=[]
    async with httpx.AsyncClient(base_url=values['url'],timeout=30) as client:
        assert (await client.get('/health')).json()=={'status':'ok'}
        assert (await client.get('/login')).status_code==200
        assert (await client.get('/api/v1/users/me')).status_code in (401,403)
        checks += ['HTTPS health/login and unauthenticated rejection']
        response=await client.post('/api/v1/auth/login',json={'email':values['email'],'password':values['password']})
        response.raise_for_status(); tokens=response.json(); token=tokens['access_token']
        client.headers['Authorization']='Bearer '+token
        workspaces=(await client.get('/api/v1/workspaces')).json()
        workspace=next(x for x in workspaces if x['slug']=='crm2-development')['id']
        for path in ['members','contacts','channels','conversations','sla/policies','flows','labels','canned-responses']:
            response=await client.get('/api/v1/workspaces/'+workspace+'/'+path)
            assert response.status_code==200,(path,response.status_code)
        checks += ['Login/workspace and core list endpoints']
        response=await client.post('/api/v1/workspaces/'+workspace+'/contacts',json={'name':'Deployment smoke fixture'})
        assert response.status_code==201,response.status_code
        contact=response.json()['id']
        response=await client.patch('/api/v1/workspaces/'+workspace+'/contacts/'+contact,json={'name':'Deployment smoke verified'})
        assert response.status_code==200
        response=await client.delete('/api/v1/workspaces/'+workspace+'/contacts/'+contact)
        assert response.status_code==204
        checks += ['Contact create/update/delete']
        content=b'%PDF-1.4 CRM2 deployment smoke'
        response=await client.post('/api/v1/media/upload',params={'workspace_id':workspace},files={'file':('deployment-smoke.pdf',content,'application/pdf')})
        assert response.status_code==200,response.status_code
        uploaded=response.json()
        assert uploaded['url'].startswith('/api/v1/media/download?')
        async with httpx.AsyncClient(timeout=30) as storage:
            downloaded=await storage.get(urljoin(values['url'],uploaded['url']));assert downloaded.status_code==200 and downloaded.content==content
            assert downloaded.headers['cache-control']=='private, no-store'
        presigned=await client.get('/api/v1/media/presign',params={'key':uploaded['key']})
        assert presigned.status_code==200
        delete_object('crm-media',uploaded['key'])
        checks += ['Owned upload/scoped download via app HTTPS and storage cleanup']
        async with websockets.connect(values['url'].replace('https://','wss://')+'/ws/'+workspace+'?token='+token) as ws:
            await ws.send('ping'); assert await asyncio.wait_for(ws.recv(),10)=='pong'
        checks += ['Authenticated public WebSocket ping/pong']
        refresh=await client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']})
        assert refresh.status_code==200 and refresh.json().get('access_token')
        checks += ['Refresh token exchange']
    result=celery_app.send_task('webhook.retry_pending',kwargs={'limit':1})
    result.get(timeout=35)
    checks += ['Real Celery queued task completed']
    print(json.dumps(checks))
asyncio.run(main(json.load(sys.stdin)))
'''
    checks.extend(json.loads(run_inside("backend", code, credentials)))
    code = r'''
import asyncio,json,httpx
from app.core.config import settings
async def main():
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.get(settings.evolution_api_url+'/instance/fetchInstances',headers={'apikey':settings.evolution_api_key})
        assert r.status_code==200,r.status_code
        print(json.dumps({'evolutionReachable':True,'instances':len(r.json())}))
asyncio.run(main())
'''
    evolution = json.loads(run_inside("backend", code))
    report = {"checks": checks, "evolution": evolution, "realWhatsAppDelivery": "pending approved number/provider credentials"}
    Path("/srv/crm2/ops/smoke-result.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
