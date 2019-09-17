import os,sys
import numpy as np

class ProgressBar(object):
    def __init__(self,total,prefix='',fill = '█',unfill='–'):
        self.total=total
        self.prefix=prefix
        self.fill=fill
        self.unfill=unfill
        fmt=str(int(np.ceil(np.log10(self.total))))
        self.count=0
        self.base=' {0} |{1}| {2:'+fmt+'}/{3:'+fmt+'} {4:4.1f}%'
        

    def __call__(self,itr,newline=True):
        logging=hasattr(sys.stdout,'logging')
        if logging:        
            sys.stdout.logging=False

        
        print('\r'+self.message(itr),end='\r')
        
        if logging:
            sys.stdout.logging=True
        
        # Print New Line on Completion
        if itr == self.total and newline: 
            print()

    def increment(self):
        self.count+=1
        self(self.count)


    def message(self,iteration):
        percent=float(iteration)/float(self.total)*100
        rows, columns = os.popen('stty size', 'r').read().split()


        
        msg=self.base.format(self.prefix,'',iteration,self.total,percent)
        
        
        length=int(columns)-len(msg)
        if length>0:
            filledLength = int(length * iteration // self.total)
            unfilledLength=length-filledLength
            bar = self.fill*filledLength + self.unfill*unfilledLength
            msg=self.base.format(self.prefix,bar,iteration,self.total,percent)
        else:
            msg=' {0} {1}/{2}'.format(self.prefix,iteration,self.total)
            
        
        return msg


if __name__=='__main__':
    from time import sleep
    n=200
    pb=ProgressBar(n,prefix='test')
    for i in range(n):
        pb.increment()
        sleep(0.01)
