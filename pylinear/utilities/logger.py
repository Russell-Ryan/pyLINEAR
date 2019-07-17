import sys
import datetime

class Logger(object):
    ''' class to perform custom logging by overriding print command '''
   

    def __init__(self,name,logfile='linear.log'):
        ''' create a log file that contains the same content as print '''
        self.terminal=sys.stdout
        try:
            self.logfile=open(logfile,'w')
            self.logging=True
        except:
            msg="Unable to write the logfile: {}.\n".format(logfile)
            self.terminal.write(msg)
            self.logging=False

        if self.logging:
            now=datetime.datetime.now()
            today=now.strftime("   %a, %b %d, %Y")
            now=now.strftime("   %I:%M:%S %p")

            label='started from module: {}:'.format(name)
            self.num=74

            self.logfile.write(' +-'+self.num*'-'+'-+\n')
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' | '+label+' '*(self.num-len(label))+' |\n')
            self.logfile.write(' | '+today+' '*(self.num-len(today))+' |\n')
            self.logfile.write(' | '+now+' '*(self.num-len(now))+' |\n')
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' +-'+self.num*'-'+'-+\n\n\n')
                

            
    def write(self,text):
        ''' override the print functionality '''

        
        self.terminal.write(text)
        if self.logging:
            self.logfile.write(text)
            
    def flush(self):
        ''' obligatory method '''

        pass

    def __del__(self):
        ''' magic method to ensure files are closed safely, append outro '''
        
        sys.stdout=self.terminal
        if self.logging:

            now=datetime.datetime.now()
            today=now.strftime("   %a, %b %d, %Y")
            now=now.strftime("   %I:%M:%S %p")

            label='finished!'
            self.logfile.write('\n\n')
            self.logfile.write(' +-'+self.num*'-'+'-+\n')
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' | '+label+' '*(self.num-len(label))+' |\n')
            self.logfile.write(' | '+today+' '*(self.num-len(today))+' |\n')
            self.logfile.write(' | '+now+' '*(self.num-len(now))+' |\n')      
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' +-'+self.num*'-'+'-+\n')
            self.logfile.close()


if __name__=='__main__':
    print('testing the logging utility')
        
    sys.stdout=Logger('Test',logfile='test.log')


