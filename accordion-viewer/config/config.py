''' Configuration file template '''

#eventbuffersize = 1000

startup = {
                            'camera_exposure_time':0.01,
                            'camera_display_live_subsampling': 2,
                            'camera_display_acquisition_subsampling':2,
                            'event_processing_enabled': True,     
            }


event_camera = 'DemoEventCamera' # 'DemoEventCamera' or 'PropheseeEventCamera' 

event_camera_parameters = { 'demo_type' : 'spiral', # or 'spiral'
                            'x_pixels' : 1024,
                            'y_pixels' : 1024,
                            'x_pixel_size_in_microns' : 6.5,
                            'y_pixel_size_in_microns' : 6.5,
                            'events_per_chunk' : 500,
                            'off_events_per_chunk' : 200,
                            'chunk_frequency_in_Hz' : 30,
                            'subsampling' : [1,2,4],
                             }

frame_camera = 'HamamatsuOrca' # 'DemoFrameCamera' or 'HamamatsuOrca'
'''

frame_camera_parameters = { 'x_pixels' : 1024,
                            'y_pixels' : 1024,
                            'x_pixel_size_in_microns' : 6.5,
                            'y_pixel_size_in_microns' : 6.5,
                            'binning' : '1x1',
                            'camera_id' : 0,
                            'sensor_mode' : 1,    # 12 for progressive
                            'defect_correct_mode': 2,
                            'binning' : '1x1',
                            'readout_speed' : 1,
                            'trigger_active' : 1,
                            'trigger_mode' : 1, # it is unclear if this is the external lightsheeet mode - how to check this?
                            'trigger_polarity' : 2, # positive pulse
                            'trigger_source' : 1, # internal
                            }
'''

frame_camera_parameters = { 'x_pixels' : 2048,
                            'y_pixels' : 2048,
                            'x_pixel_size_in_microns' : 6.5,
                            'y_pixel_size_in_microns' : 6.5,
                            'binning' : '1x1',
                            'camera_id' : 0,
                            'sensor_mode' : 1,    # 12 for progressive
                            'defect_correct_mode': 2,
                            'binning' : '1x1',
                            'readout_speed' : 2,
                            'trigger_active' : 1,
                            'trigger_mode' : 1, # it is unclear if this is the external lightsheeet mode - how to check this?
                            'trigger_polarity' : 2, # positive pulse
                            'trigger_source' : 1, # internal
                            }