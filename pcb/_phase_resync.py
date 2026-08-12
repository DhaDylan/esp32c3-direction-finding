import pcbnew, re

PCB="10.28.25 V2 Wifi PCB.kicad_pcb"
NET="_sch_netlist.net"

# ---- parse schematic netlist: (ref,pin) -> netname ----
t=open(NET,encoding="utf-8").read()
# isolate the (nets ...) section
nets_sec = t[t.index("(nets"):]
pad_net={}
net_names=set()
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|\Z)', nets_sec, re.S):
    name=m.group(1); body=m.group(2)
    net_names.add(name)
    for ref,pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', body):
        pad_net[(ref,pin)]=name
print(f"Parsed {len(net_names)} nets, {len(pad_net)} pad assignments from schematic")

b=pcbnew.LoadBoard(PCB)

# ensure all nets exist in board
existing={b.GetNetInfo().GetNetItem(c).GetNetname() for c in range(b.GetNetInfo().GetNetCount())}
added=0
for nn in sorted(net_names):
    if nn not in existing:
        ni=pcbnew.NETINFO_ITEM(b, nn)
        b.Add(ni); added+=1
print(f"Added {added} missing nets to board")

# reassign pads
changes=[]
missing_in_sch=[]
for f in b.GetFootprints():
    ref=f.GetReference()
    for p in f.Pads():
        pad=p.GetPadName()
        want=pad_net.get((ref,pad))
        if want is None:
            # pad not in schematic netlist (e.g., NC) -> leave as-is
            continue
        cur=p.GetNetname()
        if cur!=want:
            net=b.FindNet(want)
            if net is None:
                net=pcbnew.NETINFO_ITEM(b, want); b.Add(net)
            p.SetNet(net)
            changes.append((ref,pad,cur,want))

print(f"\nReassigned {len(changes)} pads. Power1-related changes:")
for ref,pad,cur,want in changes:
    if want=="/Power1" or cur=="/Power1":
        print(f"  {ref}.{pad}: {cur} -> {want}")
# summarize all by target net
from collections import Counter
c=Counter(w for *_,w in changes)
print("\nChange counts by target net:")
for k,v in c.most_common(12):
    print(f"  {v:3}  -> {k}")

b.BuildListOfNets()
pcbnew.SaveBoard(PCB,b)
print("\nSaved. Power1 now exists:", b.FindNet("/Power1") is not None)
