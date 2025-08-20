from laboneq.simple import *
import matplotlib.pyplot as plt
import numpy as np
import laboneq

class PunchOut:
    def __init__ (self):
        print(laboneq.__version__)
    
    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 5,
                         acq_freq_sweep = LinearSweepParameter(uid='acq_freq_sweep_default', 
                                                                 start=-100e6,
                                                                 stop=100e6,
                                                                 count=2001),
                         acq_amp_sweep = LinearSweepParameter(uid='acq_amp_sweep_default',
                                                              start=0.1,
                                                              stop=0.7,
                                                              count=101),
                         integration_length = 1e-6):
        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
            ],
        )

        with exp.sweep(uid="acq_amp_sweep", parameter=acq_amp_sweep):
            aaa