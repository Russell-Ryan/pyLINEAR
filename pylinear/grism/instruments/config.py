import os
import pysiaf
import xml.etree.ElementTree as ET
import numpy as np
from astropy.io import fits

        
DTYPE={'float64':np.float64,'float32':np.float32,           
       'int64':np.int64,'int32':np.int32,'int16':np.int16,
       'uint64':np.uint64,'uint32':np.uint32,'uint16':np.uint16}

class SIP(object):
    def __init__(self,element,comp):
        self.comp=comp
        self.order=0
        self.data={}
        for el in element.findall(comp):
            i,j=int(el.attrib['i']),int(el.attrib['j'])
            self.order=max(self.order,i,j)
            self.data[(i,j)]=float(el.text)

    def update_header(self,hdr):
        if self.data:
            hdr['{}_order'.format(self.comp)]=self.order
            label=self.comp+'_{}_{}'
            for k,v in self.data.items():
                hdr[label.format(*k)]=v
                
    def __bool__(self):
        return len(self.data)!=0
                
    def __str__(self):
        return "SIP distortion model of {}".format(self.comp)

                
class SIAF(object):
    def __init__(self,siaf_element):
        attrib=siaf_element.attrib
        
        # set a bunch of things for the self
        self.naxis=(int(attrib['naxis1']),int(attrib['naxis2']))
        self.crpix=(float(attrib['crpix1']),float(attrib['crpix2']))
        self.v2=float(attrib['v2'])
        self.v3=float(attrib['v3'])
        self.v3y=float(attrib['v3y'])
        self.xscl=float(attrib['xscl'])
        self.yscl=float(attrib['yscl'])

        # set the SIP parameters
        self.a=SIP(siaf_element,'a')
        self.b=SIP(siaf_element,'b')
        self.ap=SIP(siaf_element,'ap')
        self.bp=SIP(siaf_element,'bp')

        
    def make_header(self,crval1,crval2,orientat,refsiaf=None):
        if refsiaf is None:
            refsiaf=self

        # based on Bryan Hilbert's email from Apr 15, 2020, I should
        # transform orientat to a local_roll, but that is really
        # complicated.  But the first order is:
        # local_roll=-orientat-self.v3y
        # is essentially that.  Higher order will require more coding.
        local_roll=-orientat-self.v3y
        A = pysiaf.rotations.attitude(refsiaf.v2, refsiaf.v3, 
                                      crval1, crval2, local_roll)

        # compute the new positions
        crvals = pysiaf.utils.rotations.pointing(A, self.v2, self.v3)

        # compute rotation matrix
        cs=np.cos(orientat*np.pi/180)
        sn=np.sin(orientat*np.pi/180)
        R=np.array([[cs,-sn],[sn,cs]])

        # compute a pixel matrix
        P=np.array([[-self.xscl/3600,0],[0,self.yscl/3600.]])

        # compute CD matrix as dot product
        CD=np.dot(R,P)

        # test if sip is present
        suffix='-SIP' if any([self.a,self.b,self.ap,self.bp]) else ''
        
        # make a fits Header
        hdr=fits.Header()
        hdr['NAXIS1']=(self.naxis[0],'number of pixels in x')
        hdr['NAXIS2']=(self.naxis[1],'number of pixels in y')
        hdr['CRPIX1']=(self.crpix[0],'x-coordinate of reference pixel')
        hdr['CRPIX2']=(self.crpix[1],'y-coordinate of reference pixel')
        hdr['CRVAL1']=(crvals[0],'first axis value at reference pixel')
        hdr['CRVAL2']=(crvals[1],'second axis value at reference pixel')        
        hdr['CD1_1']=(CD[0,0],'partial of first axis coordinate w.r.t. x')
        hdr['CD1_2']=(CD[1,0],'partial of first axis coordinate w.r.t. y')
        hdr['CD2_1']=(CD[0,1],'partial of second axis coordinate w.r.t. x')
        hdr['CD2_2']=(CD[1,1],'partial of second axis coordinate w.r.t. y')
        hdr['CTYPE1']=('RA---TAN'+suffix,'the coordinate type for the first axis')
        hdr['CTYPE2']=('DEC--TAN'+suffix,'the coordinate type for the second axis')
        hdr['EQUINOX']=(2000.,'equinox of coordinates')
        hdr['LATPOLE']=(90.,' ')
        hdr['LONGPOLE']=(180.,' ')
        hdr['ORIENTAT']=(-orientat,'position angle of image y axis (deg. e of n)')
        # update the SIP parameters
        self.a.update_header(hdr)
        self.b.update_header(hdr)
        self.ap.update_header(hdr)
        self.bp.update_header(hdr)

        return hdr
        


class Extension(object):
    def __init__(self,element):
        self.name=element.attrib['type']
        self.extname=element.attrib['name']
        self.extver=int(element.attrib['ver'])
        self.dtype=DTYPE[element.attrib['dtype']]
        self.number=int(element.text)
        
    def __str__(self):
        tokens=['{} Extension:'.format(self.name),
                'NAME    = {}'.format(self.extname),
                'VERSION = {}'.format(self.extver),
                'NUMBER  = {}'.format(self.number),
                'DTYPE   = {}'.format(self.dtype)]
        return '\n'.join(tokens)
        

class Header(object):
    def __init__(self,element):
        self.data={}
        for el in element.findall('header'):
            self.data[el.attrib['keyword']]=(el.text,el.attrib['comment'])
        
    def update_header(self,hdr,stanza=None): 
        after=list(hdr.keys())[-1]
        first=after
        for k,v in self:
            if isinstance(v,(tuple,list)):
                hdr.set(k,value=v[0],comment=v[1],after=after)
            else:
                hdr.set(k,value=v[0],after=after)
            after=k
            #hdr[k]=v
        if stanza is not None:
            hdr.set('',value='',after=first)
            hdr.set('',value='      / {}'.format(stanza),after=first)
            hdr.set('',value='',after=first)
            
    def __setitem__(self,k,v):
        self.data[k]=v

    def __getitem__(self,k):
        return self.data[k]

            
    def __iter__(self):
        yield from self.data.items()

    def __str__(self):
        lines=['{0:8s}= {1} \ {2}'.format(k,v[0],v[1]) for k,v in self]
        return '\n'.join(lines)
    
    def __len__(self):
        return len(self.data)

    

class Device(object):
    def __init__(self,dev_element):
        self.name=dev_element.attrib.get('name','')
        self.bitmask=int(dev_element.attrib.get('bitmask','0'))

        
        # load the grisms
        self.grisms={}
        for grism_element in dev_element.findall('grism'):
            grism=Grism(grism_element)
            self.grisms[grism.name]=grism
            #grism=grism_element.attrib.get('grism',None)
            #block=grism_element.attrib.get('blocking',None)
            #path=grism_element.attrib.get('path','')
            #self.grisms[(grism,block)]=os.path.join(path,grism_element.text)

        # load extensions
        self.extensions={}
        for ex_element in dev_element.findall('extension'):
            exten=Extension(ex_element)
            self.extensions[exten.name]=exten
            
        # load the SIAF
        self.siaf=SIAF(dev_element.find('siaf'))
            
        # load any header keywords
        self.header=Header(dev_element)
        
    def make_header(self,*args,**kwargs):
        return self.siaf.make_header(*args,**kwargs)

    def grism_config(self,grism):
        try:
            conf=self.grisms[grism].config
        except KeyError:
            print("[warn]grism/block combination not valid: {}.".format(grism))
        return conf
            
    def extension(self,exten):
        return self.extensions[exten]    
    
    def __str__(self):
        return "Device configuration for {}".format(self.name)


class Grism(object):
    def __init__(self,grism_element):
        self.grism=grism_element.attrib.get('grism',None)
        self.block=grism_element.attrib.get('blocking',None)
        self.path=grism_element.attrib.get('path','')
        self.lamb0=float(grism_element.attrib.get('lamb0',None))
        self.lamb1=float(grism_element.attrib.get('lamb1',None))
        self.dlamb=float(grism_element.attrib.get('dlamb',None))
        self.config=os.path.join(self.path,grism_element.text)
        self.name=(self.grism,self.block)

        
class Detector(object):
    def __init__(self,det_element):
        self.name=det_element.attrib.get('name','')

        self.refsiaf=det_element.attrib.get('refsiaf',None)

        
        self.devices={}
        for dev_element in det_element.findall('device'):
            device=Device(dev_element)
            self.devices[device.name]=device

        self.header=Header(det_element)

        
    def __iter__(self):
        yield from self.devices.values()

    def __str__(self):
        return "Detector configuration for {}".format(self.name)

    def __getitem__(self,k):
        return self.devices[k]


class Instrument(object):
    def __init__(self,ins_element):
        self.name=ins_element.attrib['name']

        self.detectors={}
        for det_element in ins_element:
            detector=Detector(det_element)
            self.detectors[detector.name]=detector

            
    def __str__(self):
        return 'Instrument configuration for {}'.format(self.name)

    def __getitem__(self,k):
        return self.detectors[k]
            
    
class Config(object):
    def __init__(self,telescope,xmlfile=None):
        if xmlfile is None:
            path=os.path.dirname(__file__)
            if path=='':
                path='.'
            xmlfile=path+os.sep+'instruments.xml'

        # record the telesocpe
        self.telescope=telescope
        
        # open the XML
        tree=ET.parse(xmlfile)
        conf=tree.getroot()

        # get the attributes 
        self.attrib=conf.attrib
        
        # get the telescope element
        t=[tel.attrib['name'] for tel in conf]
        tel_element=conf[t.index(self.telescope)]

        # read all the instruments for this telescope
        self.instruments={}
        for ins_element in tel_element.findall('instrument'):
            instrument=Instrument(ins_element)
            self.instruments[instrument.name]=instrument

    def __str__(self):
        return "Instrumental configuration for {}".format(self.telescope)
        
    def __getitem__(self,k):
        return self.instruments[k]
        
if __name__=='__main__':
    x=Config('HST')
    print(x)


    #print(x['NIRISS']['NIRISS']['NIRISS'].grism_config(('GR150C','F090W')))
    #    print(x['WFC3']['IR']['IR'].grism_config(('G102',None)))
    
    '''
    ref=x['WFC3']['UVIS']['UVIS1'].siaf
    h2=x['WFC3']['UVIS']['UVIS2'].make_header(84.711868,-69.112998,-165.947,refsiaf=ref)
    print(h2['CRVAL1'],h2['CRVAL2'])
    
    ref=x['WFC3']['UVIS']['UVIS2'].siaf
    h1=x['WFC3']['UVIS']['UVIS1'].make_header(h2['CRVAL1'],h2['CRVAL2'],-166.098,refsiaf=ref)

    print(h1['CRVAL1'],h1['CRVAL2'])
    
    img=np.zeros((1014,1014))

    from astropy.io import fits
    fits.writeto('test.fits',img,header=h1,overwrite=True)
    
    '''
    #for q in x['WFC3']['UVIS']:
    #    print(q)
    
