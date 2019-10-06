# Items To Do.

1. change the way progress bar is dealt with.  use the tqdm as Nor suggested.

```
 mypool = Pool(10) 

   res = []
   for i,pp in enumerate(tqdm(mypool.imap_unordered(do_one,pars),total=len(pars),desc="Optimizing Redshift")):
       res.append(pp)

   mypool.close() # No more work
   mypool.join()

```

but can probably join an iteratable list with constant data via map:
```
class Test(object):
    def __init__(self,x):
        self.x=x


if __name__=='__main__':
    objs=[Test(x) for x in range(1000)]
    other=Test(1000)
    otherother=Test(2000)

    q=map(lambda e: (e,other,otherother),objs)
    print(sys.getsizeof(q))

```

2. add the masking

3. pixfrac in the drizzling

~~4. create residuals~~


