import sys
import datetime
import re

class Logger(object):
    ''' class to perform custom logging by overriding print command '''
   

    def __init__(self,name,logfile=None,time=True):
        ''' create a log file that contains the same content as print '''

        if logfile is None:
            logfile=name.lower()+'.log'

        self.time=time
            
        # define the regex search tool
        #self.regex=re.compile('\<(.*?)\>')
        self.regex=re.compile('\[[A-Za-z]+\]')

        
        
        self.stdout=sys.stdout
        try:
            self.logfile=open(logfile,'w')
            self.logging=True
        except:
            msg="Unable to write the logfile: {}.\n".format(logfile)
            self.stdout.write(msg)
            self.logging=False

        if self.logging:
            now=datetime.datetime.now()
            today=now.strftime("   %a, %b %d, %Y")
            now=now.strftime("   %I:%M:%S %p")

            label='started from module: {}:'.format(name)
            self.num=74    # so that it fits in default windows

            self.logfile.write(' +-'+self.num*'-'+'-+\n')
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' | '+label+' '*(self.num-len(label))+' |\n')
            self.logfile.write(' | '+today+' '*(self.num-len(today))+' |\n')
            self.logfile.write(' | '+now+' '*(self.num-len(now))+' |\n')
            self.logfile.write(' | '+self.num*' '+' |\n')
            self.logfile.write(' +-'+self.num*'-'+'-+\n\n\n')
            self.logfile.flush()

            
    def write(self,text):
        ''' override the print functionality '''

        # get the time
        if self.time:
            now=datetime.datetime.now().strftime(" %b/%d/%y-%H:%M:%S")
        else:
            now=''
            
        #https://www.geeksforgeeks.org/print-colors-python-terminal/
        #self.stdout.write("\033[91m{}\033[00m".format(text)) 

        # sort out the logging level and print to the screen
        match=self.regex.match(text)
        if match:
            ttype=match.group(0)
            if ttype=='[info]': f="\033[32;1mInfo>\033[00m\033[32m {}\033[00m"
            elif ttype=='[warn]':f="\033[33;1mWarning>\033[0m\033[33m {}\033[0m"
            elif ttype=='[alarm]': f="\033[31;1mAlarm> \033[5m{}\033[00m"
            elif ttype=='[debug]': f="\033[36;3mDebug> {}\033[00m"
            #elif ttype=='[title]': f="\033[30;1m{}{}\033[00m"
            else: f='{}'
            self.stdout.write(f.format(text[match.end(0):]))
        else:
            self.stdout.write(text)
        
        
        # print to the log file?
        if self.logging:
            if match:
                ttype=match.group(0)
                if ttype=='[info]': f="[info{}] {}"
                elif ttype=='[warn]':f="[warn{}] {}"
                elif ttype=='[alarm]': f="[alarm{}] {}"
                elif ttype=='[debug]': f="[debug{}] {}"
                #elif ttype=='[title]': f="[{}] {}"
                else: f='[{}] {}'
                self.logfile.write(f.format(now,text[match.end(0):]))
            else:
                self.logfile.write(text)
            self.logfile.flush()

        # original printing
        #self.stdout.write(text)
        #if self.logging:
        #    self.logfile.write(text)
        #    self.logfile.flush()
        
    def flush(self):
        ''' obligatory method '''
        pass

    def __del__(self):
        ''' magic method to ensure files are closed safely, append outro '''
        
        sys.stdout=self.stdout    # reset the stdout
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

    import numpy as np
    
    sys.stdout=Logger('Test',logfile='test.log')
    
    print('[info]This is informational')
    print('[warn]This is slightly more worrisome')
    print('[alarm]This is alarming')
    print('[debug]a debugging message')
    print('[title]A title message')
    print('this is a standard')
    print('[warn]',[1,2,34])
