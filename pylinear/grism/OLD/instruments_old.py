import xml.etree.ElementTree as ET
import os


class Grism(object):
    def __init__(self,element):
        attrib=element.attrib
        self.grism=attrib['grism']
        self.config=element.text
        self.blocking=attrib.get('blocking',None)
        
        
class Header(object):
    def __init__(self):
        self.data={}
    def from_xml(self,element):
        attrib=element.attrib
        self[attrib['keyword']]=(element.text,attrib['comment'])

    def __setitem__(self,k,v):
        # parse the input
        if isinstance(v,tuple):
            c=v[1]
            v=v[0]
        else:
            c=''

        # try to retype it
        try:
            v=int(v)
        except:
            try:
                v=float(v)
            except:
                pass

        # record the keyword,(value,comment) pair
        self.data[k]=(v,c)
    def __len__(self):
        return len(self.data)

        
    def items(self):
        return self.data.items()
    
    def __str__(self):
        out='Header Values:'
        if len(self)==0:
            out+='\nis empty'
        else:
            for k,(v,c) in self.items():
                if isinstance(v,str):
                    v="'"+v+"'"
                out+='\n{:8}= {} / {}'.format(k,v,c)
        return out
        
class Module(object):
    def __init__(self,module,path):
        self.name=module.attrib['name']

        self.path=os.path.join(path,self.name)
        
        # load some grisms
        self.grisms={}
        for g in module.findall('grism'):
            grism=Grism(g)
            self.grisms[(grism.grism,grism.blocking)]=grism

        # load the SIAF data
        self.siaf=module.findall('siaf')[0].attrib
        header=module.findall('header')

        # load some header keywords
        self.header=Header()
        for h in module.findall('header'):
            self.header.from_xml(h)

        # load the fits extensions
        exten=module.findall('extensions')[0].attrib
        self.exten={k:int(v) for k,v in exten.items()}


    def load_config(self,grism,blocking):
        k=(grism,blocking)
        if k in self.grisms:
            filename=os.path.join(self.path,grism,self.grisms[k].config)
            print("LOADING {}".format(filename))
            conf=True

        else:
            conf=None
            
        return conf
        
    def __str__(self):
        return "Grism module {}".format(self.name)

    def __getitem__(self,k):
        return self.grisms[k]

    def __contains__(self,k):
        return k in self.grisms

    
class Detector(object):
    def __init__(self,telescope,instrument,detector):
        attrib=detector.attrib
        self.name=attrib['name']


        path=os.path.join(telescope.name,instrument.name,self.name)

        
        self.header=Header()
        self.header['TELESCOP']=(telescope.name,'telescope used to acquire data')
        self.header['INSTRUME']=(instrument.name,'identifier for instrument used to acquire data')
        for h in detector.findall('header'):
            self.header.from_xml(h)

        self.modules=[Module(el,path) for el in detector.findall('module')]
        
    def __str__(self):
        return "Detector configuration for {}".format(self.name)

    def __iter__(self):
        yield from self.modules

    
        
class Instrument(object):
    def __init__(self,module):
        self.name=module.attrib['name']

class Telescope(object):
    def __init__(self,module):
        self.name=module.attrib['name']


        
class Config(dict):
    def __init__(self):
        tree=ET.parse('instruments.xml')
        conf=tree.getroot()

        for telescope in conf:
            t=Telescope(telescope)
            for instrument in telescope:
                i=Instrument(instrument)
                for detector in instrument:
                    d=Detector(t,i,detector)
                    self[(t.name,i.name,d.name)]=d
                    #i[d.name]=d
                #t[i.name]=i
            #self[t.name]=t
        
    def get(self,telescope,instrument,detector):
        try:
            modules=self[(telescope,instrument,detector)]
        except:
            raise KeyError("Invalid ({},{},{}) tuple.".format(telescope,instrument,detector))

        return modules


if __name__=='__main__':



    tree=ET.parse('instruments.xml')
    conf=tree.getroot()


    t=[tel.attrib['name'] for tel in conf]
    tel=conf[t.index('HST')]

    i=[ins.attrib['name'] for ins in tel]
    ins=tel[i.index('WFC3')]

    d=[det.attrib['name'] for det in ins]
    det=Detector(Telescope(tel),Instrument(ins),ins[d.index('IR')])




    x=Config()

    detector=x.get('HST','WFC3','IR')



    print(det.name,detector.name)
    print(type(detector),type(det))

    kjf


    print("STUFF WITH PHDU")    
    for m in detector:
        print("PROCESS EACH DETECTOR")
        conf=m.load_config('g102',None)

    detector=x.get('JWST','NIRCAM','LONG')

    print("STUFF WITH PHDU")    
    for m in detector:
        print("PROCESS EACH DETECTOR")
        conf=m.load_config('column','F480M')


        #detector=x.get('HST','WFC3','IR','g102')
    #for m in detector:
    #    print(m.grisms)
#
