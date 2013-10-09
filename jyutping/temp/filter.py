charset = set([x.rstrip() for x in open('cnewuniq')])
a = open('jnewadd', 'w')
d = open('jnewdiff', 'w')
for x in open('jnewuniq'):
    t = x.rstrip().split()
    if t[0] in charset:
        print >> a, x,
    else:
        print >> d, x,
