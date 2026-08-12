import json
d=json.load(open("_drc_clean.json"))
RFW={'Net-(C17-Pad1)':0.3,'Net-(U4-LNA_IN)':0.3,'Net-(U3-LNA_IN)':0.3,'Net-(C24-Pad1)':0.3,
     'Net-(U5-LNA_IN)':0.3,'Net-(C36-Pad1)':0.3}
segs=[]
for v in d['unconnected_items']:
    its=v['items']
    if len(its)!=2: continue
    # both endpoints must be pads (skip zone endpoints -> those are plane fanout)
    if any('Zone' in i['description'] for i in its): continue
    net=None
    for i in its:
        de=i['description']
        if '[' in de: net=de.split('[')[1].split(']')[0]
    p1=its[0]['pos']; p2=its[1]['pos']
    w=RFW.get(net,0.25)
    segs.append((p1['x'],p1['y'],p2['x'],p2['y'],net,w))
json.dump({"segs":segs},open("_gaps.json","w"))
print(f"pad-pad gaps to route: {len(segs)}")
for s in segs: print("  ",s[4],round((s[0]-s[2])**2+(s[1]-s[3])**2,1)**0.5,"mm")
