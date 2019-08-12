import os,sys

class ProgressBar(object):
    def __init__(self,total,prefix = '', suffix = '', decimals = 1,
                 length = 100, fill = '█',unfill='–'):
        self.total=total
        self.decimals=decimals
        self._prefix=prefix
        self._suffix=suffix
        self.fill=fill
        self.unfill=unfill
        self.setLength()
        self.count=0       # the current increment

        
    @property
    def prefix(self):
        return self._prefix
    @prefix.setter
    def prefix(self,pre):
        self._prefix=pre
        self.setLength()

    @property
    def suffix(self):
        return self._suffix
    @suffix.setter
    def suffix(self,suf):
        self._suffix=suf
        self.setLength()
    
        
    def setLength(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        self.length=0
        a=str(self.decimals+4)    # 1 for . and 3 for leading digits
        b=str(self.decimals)
        
        self.string="{0:"+a+"."+b+"f}"
        msg=self.message(0)
        self.length=int(columns)-len(msg)
        if self.length <= 0:
            raise ValueError("Length must be a positive integer.")

        

    def percentage(self,iteration):
        percent=(float(iteration)/float(self.total))*100.
        percent = self.string.format(percent)
        return percent

    def message(self,iteration):
        percent=self.percentage(iteration)
        filledLength = int(self.length * iteration // self.total)
        unfilledLength=self.length-filledLength
        bar = self.fill*filledLength + self.unfill*unfilledLength
        
        return '\r{} |{}| {}% {}'.format(self.prefix,bar,percent,self.suffix)

    
    def __call__(self,iteration,newline=True,resize=True):

        logging=hasattr(sys.stdout,'logging')
        if logging:        
            sys.stdout.logging=False

        print(self.message(iteration),end='\r')
        
        if logging:
            sys.stdout.logging=True
        
        # Print New Line on Completion
        if iteration == self.total and newline: 
            print()

            
    def increment(self):
        self.count+=1
        self(self.count)

def test(obj,progressbar=None):
    from time import sleep
    #for i in range(n):
    #count=itr[0]
    #obj=itr[1]
    
    if progressbar is not None:
        progressbar.increment()
    sleep(0.05)

    return obj

        
if __name__=='__main__':
    
    import pool

    n=100
    pb=ProgressBar(n,suffix='1')
    #for i in range(n):
    #    pb(i+1,newline=False)
    #    sleep(0.05)
    #
    #pb.suffix='2'
    #for i in range(n):
    #    pb(i+1,newline=False)
    #    sleep(0.05)
    iters=[i for i in range(n)]
    pool.pool(test,iters,ncpu=2)
    
