#!/usr/bin/python3
import argparse,json,time
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--request');p.add_argument('--events');p.add_argument('--reply');a=p.parse_args()
if a.check: print(json.dumps({'ready':True,'note':'fixture'}));raise SystemExit(0)
with open(a.events,'w') as f:f.write(json.dumps({'kind':'started','turn_id':'fixture-turn','account':'fixture@example.invalid'})+'\n');f.write(json.dumps({'kind':'progress','view':{'turn_id':'fixture-turn','stage':'waiting_editor','steps':[],'editor_request':{'id':'read-1','class':'ReadBuffer','fields':{'path':'a.code'}}}})+'\n')
print('event',flush=True)
time.sleep(60)
