"""
Helper classes for acquisitions
"""

import indexed

class Acquisition(indexed.IndexedOrderedDict):
    '''
    Custom acquisition dictionary

    Can be used as:

    acq1 = Acquisition( x_pos=30,
                 y_pos=10,
                 z_start=0,
                 z_end=6000,
                 z_step=2,
                 theta_pos=0,
                 f_pos=0,
                 laser='488 nm',
                 intensity=50,
                 filter='488LP',
                 zoom='1x',
                 filename='')

    Getting keys:

    keys = [key for key in acq1.keys()]
    print(keys)

    '''

    def __init__(self,
                 x_pos=0,
                 y_pos=0,
                 z_start=0,
                 z_end=100,
                 z_step=1,
                 theta_pos=0,
                 f_pos=0,
                 laser = '488 nm',
                 intensity=0,
                 filter= '515LP',
                 zoom= '1x',
                 shutter='Left',
                 filename=''):

        super().__init__()

        self['x_pos']=x_pos
        self['y_pos']=y_pos
        self['z_start']=z_start
        self['z_end']=z_end
        self['z_step']=z_step
        self['rot']=theta_pos
        self['f_pos']=f_pos
        self['laser']=laser
        self['intensity']=intensity
        self['filter']=filter
        self['zoom']=zoom
        self['shutter']=shutter
        self['filename']=filename


    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __call__(self, index):
        ''' This way the dictionary is callable with an index '''
        return self.values()[index]

    def get_keylist(self):
        ''' Here, a list of capitalized keys is return for usage as a table header '''
        return [key.capitalize() for key in self.keys()]

    def get_image_count(self):
        '''
        Method to return the number of planes in the acquisition
        '''
        image_count = abs(int((self['z_end'] - self['z_start'])/self['z_step']))

        return image_count

    def get_acquisition_time(self):
        '''
        Method to return the time in seconds the acquisition will take

        TODO: Implement properly
        '''
        return cfg.sweeptime * self.get_image_count()

    def get_zoom(self):
        return self['zoom']

    def get_filter(self):
        return self['filter']

    def get_laser(self):
        return self['laser']

    def get_intensity(self):
        return self['intensity']

    def get_filename(self):
        return self['filename']

    def get_delta_z_dict(self):
        ''' Returns relative movement dict for z-steps '''
        if self['z_end'] > self['z_start']:
            z_rel = abs(self['z_step'])
        else:
            z_rel = -abs(self['z_step'])

        return {'z_rel' : z_rel}

    def get_startpoint(self):
        '''
        Provides a dictionary with the startpoint coordinates
        '''
        return {'x_abs': self['x_pos'],
                'y_abs': self['y_pos'],
                'z_abs': self['z_start'],
                'theta_abs': self['rot'],
                'f_abs': self['f_pos'],
                }

    def get_endpoint(self):
        return {'x_abs': self['x_pos'],
                'y_abs': self['y_pos'],
                'z_abs': self['z_end'],
                'theta_abs': self['rot'],
                'f_abs': self['f_pos'],
                }

    def get_midpoint(self):
        return {'x_abs': self['x_pos'],
                'y_abs': self['y_pos'],
                'z_abs': int((self['z_end']-self['z_start'])/2),
                'theta_abs': self['rot'],
                'f_abs': self['f_pos'],
                }



class AcquisitionList(list):
    '''
    Class for a list of acquisition objects

    Examples: "([acq1,acq2,acq3])" is due to the fact that list takes only a single argument
    acq_list = AcquisitionList([acq1,acq2,acq3])
    acq_list.time()
    > 3600
    acq_list.planes()
    > 18000

    acq_list[2](2)
    >10
    acq_list[2]['y_pos']
    >10
    acq_list[2]['y_pos'] = 34


    '''
    def __init__(self, *args):
        list.__init__(self, *args)

        ''' If no arguments are provided, create a
        default acquistion in the list '''

        if len(args) == 0:
            ''' Use a default acquistion '''
            self.append(Acquisition())

    def get_keylist(self):
        '''
        Here, a list of capitalized keys is returnes for usage as a table header
        '''
        return self[0].get_keylist()

    def get_acquisition_time(self):
        '''
        Returns total time in seconds of a list of acquisitions
        '''
        time = 0

        for i in range(len(self)):
            time += self[i].get_acquisition_time()

        return time

    def get_image_count(self):
        '''
        Returns the total number of planes for a list of acquistions
        '''
        image_count = 0
        for i in range(len(self)):
            image_count += self[i].get_image_count()

        return image_count

    def get_startpoint(self):
        return self[0].get_startpoint()
