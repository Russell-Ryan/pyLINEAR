


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
    
