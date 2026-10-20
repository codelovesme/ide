#!/usr/bin/python3
import argparse,json,os,time
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--request');p.add_argument('--events');p.add_argument('--reply');p.add_argument('--account-file')
p.add_argument('--login',action='store_true');p.add_argument('--switch',action='store_true');p.add_argument('--result');a=p.parse_args()
if a.login:
    # Stands in for the browser handoff; the real one is covered by test_mike_bridge.py and mike-e2e.py.
    account='switched@example.invalid' if a.switch else 'fixture@example.invalid'
    with open(a.account_file,'w') as f:json.dump({'account':account},f)
    with open(a.result,'w') as f:json.dump({'signed_in':True,'account':account,'note':'Signed in as '+account},f)
    raise SystemExit(0)
if a.check:
    account=json.load(open(a.account_file)).get('account') if a.account_file and os.path.exists(a.account_file) else ''
    print(json.dumps({'ready':bool(account),'note':'ready · '+account if account else 'Signed out of IDE'}));raise SystemExit(0)
with open(a.events,'w') as f:f.write(json.dumps({'kind':'started','turn_id':'fixture-turn','account':'fixture@example.invalid'})+'\n');f.write(json.dumps({'kind':'progress','view':{'turn_id':'fixture-turn','stage':'waiting_editor','steps':[],'editor_request':{'id':'read-1','class':'ReadBuffer','fields':{'path':'a.code'}}}})+'\n')
print('event',flush=True)
time.sleep(60)
