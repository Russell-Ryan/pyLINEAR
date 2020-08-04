import xml.etree.ElementTree as ET
import os
import numpy as np
from collections import namedtuple


DTYPE={'float64':np.float64,'float32':np.float32,           
       'int64':np.int64,'int32':np.int32,'int16':np.int16,
       'uint64':np.uint64,'uint32':np.uint32,'uint16':np.uint16}
Extension=namedtuple('Extension',['name','ver','dtype'])

#class Extension(object):
#    def __init__(self,attrib):
#        self.name=attrib['name']
#        self.ver=int(attrib['ver'])
#        self.dtype=DTYPE[attrib['dtype'].lower()]
        

        
class Header(object):
    def __init__(self):
        self.header={}
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
        self.header[k]=(v,c)

    def update_header(self,hdr):
        for k,v in self.header.items():
            hdr[k]=v
        
    def __len__(self):
        return len(self.header)

        
    def items(self):
        return self.header.items()
    
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



class Grism(object):
    def __init__(self,element):
        attrib=element.attrib
        self.grism=attrib['grism']
        self.config=element.text
        self.blocking=attrib.get('blocking',None)

        self.header=Header()
        self.header['FILTER']=(self.grism,'element selected from filter wheel')

        self.name=(self.grism,self.blocking)
        
    def __str__(self):
        return 'Configuration for {} and {}'.format(self.grism,self.blocking)
    

class Device(object):
    def __init__(self,device,path):
        self.name=device.attrib['name']
        
        self.path=os.path.join(path,self.name)


        # check for the bitmask keyword
        self.bitmask=int(device.attrib.get('bitmask',0))
        
        # load some grisms
        self.grisms={}
        for g in device.findall('grism'):
            grism=Grism(g)
            self.grisms[grism.name]=grism

        # load the SIAF data
        self.siaf=device.findall('siaf')[0].attrib

        # load some header keywords
        header=device.findall('header')
        self.header=Header()
        for h in device.findall('header'):
            self.header.from_xml(h)
        
            
        # load the fits extensions
        self.exten={}
        for ext in device.findall('extension'):
            attrib=ext.attrib
            self.exten[attrib['type']]=Extension(attrib['name'],
                                                 int(attrib['ver']),
                                                 DTYPE[attrib['dtype']])
        
    def update_header(self,hdr):
        self.header.update_header(hdr)

    
    def config_file(self,grism,blocking):        
        k=(grism,blocking)
        if k in self.grisms:
            filename=os.path.join(self.path,grism,self.grisms[k].config)
            if not os.path.exists(filename):
                print('[warn]Grism config file does not exist')
                filename=None
        else:
            print('[warn]Grism/blocking not valid.')
            filename=None
            
        return filename
        
    def __str__(self):
        return "Grism device {}".format(self.name)

    def __getitem__(self,k):
        return self.grisms[k]

    def __contains__(self,k):
        return k in self.grisms

    def items(self):
        return self.grisms.items()

    def __iter__(self):
        yield from self.grisms.values()

    def __len__(self):
        return len(self.grisms)

    def __contains__(self,grism):
        return grism in self.grisms
        

class Detector(object):
    def __init__(self,telescope,instrument,detector):
        attrib=detector.attrib
        self.name=attrib['name']


        # initialize the header
        self.header=Header()
        self.header['TELESCOP']=(telescope,'telescope used to acquire data')
        self.header['INSTRUME']=(instrument,'identifier for instrument used to acquire data')
        self.header['DETECTOR']=(self.name,'')
        self.header['OBSTYPE']=('SPECTROSCOPIC',
                                'observation type - imaging or spectroscopic')

        for h in detector.findall('header'):
            self.header.from_xml(h)


            
        # specify the path to the config data
        confpath=os.path.join(os.environ['PYLINEAR_CONFIG'],telescope,instrument,self.name)
        
        # load all the devices
        self.devices={}
        for d in detector.findall('device'):
            device=Device(d,confpath)
            self.devices[device.name]=device
            
        
    def __str__(self):
        return "Detector configuration for {}".format(self.name)

    def __len__(self):
        return len(self.devices)

    def items(self):
        return self.devices.items()
    
    def __iter__(self):
        yield from self.devices.values()



def load_detector(telescope,instrument,detector,xmlfile=None):
    # get the name of the XML file
    if xmlfile is None:
        path=os.path.dirname(__file__)
        if path=='':
            path='.'
        xmlfile=os.path.join(path,'instruments.xml')
        
    # read the XML data
    tree=ET.parse(xmlfile)
    conf=tree.getroot()

    # force the typing
    telescope=telescope.upper()
    instrument=instrument.upper()
    detector=detector.upper()

    # get the telescope element
    t=[tel.attrib['name'] for tel in conf]
    tel_element=conf[t.index(telescope)]

    # get the instrument element
    i=[ins.attrib['name'] for ins in tel_element]
    ins_element=tel_element[i.index(instrument)]

    # get the detector element
    d=[det.attrib['name'] for det in ins_element]
    det_element=ins_element[d.index(detector)]

    # load detector data
    det=Detector(telescope,instrument,det_element)


    return det
    
if __name__=='__main__':
    
    detector=load_detector('HST','WFC3','IR')
    #print('do stuff with PHDU\n')
    print(detector,len(detector))
    for device in detector:

        conf=device.config_file('G102',None)
        print(conf)
        #for grism in device:
        #    print(device.name,grism.name)
