


class Manifest(object):
    def __init__(self):
        self.data={}
        self.data['hst_acs_f435w.filt']={'name':'F435W','zero':25.669}
        self.data['hst_acs_f606w.filt']={'name':'F606W','zero':26.502}
        self.data['hst_acs_f775w.filt']={'name':'F775W','zero':25.671}
        self.data['hst_acs_f814w.filt']={'name':'F814W','zero':25.949}
        self.data['hst_acs_f850lp.filt']={'name':'F850LP','zero':24.862}
        self.data['hst_acs_f105w.filt']={'name':'F105W','zero':26.2687}
        self.data['hst_acs_f110w.filt']={'name':'F110W','zero':26.8223}
        self.data['hst_acs_f125w.filt']={'name':'F125W','zero':26.2303}
        self.data['hst_acs_f140w.filt']={'name':'F140W','zero':26.4524}
        self.data['hst_acs_f160w.filt']={'name':'F160W','zero':25.9463}


    def __getitem__(self,key):
        return tuple(self.data[key].values())
