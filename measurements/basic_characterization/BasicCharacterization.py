# Copyright (c) 2025 Runzhao Guo. All rights reserved.
# This code is licensed for personal and educational use only.


from laboneq.simple import *
import matplotlib.pyplot as plt
import numpy as np
import laboneq

class PunchOut:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9
        self.acq_freq_sweep_cnt = 501
        self.acq_freq_sweep_start = (self.acq_res_freq - 100e6) - self.acq_lo_freq
        self.acq_freq_sweep_stop = (self.acq_res_freq + 100e6) - self.acq_lo_freq
        
        self.acq_freq_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.acq_freq_sweep_start, 
                                                      stop=self.acq_freq_sweep_stop, 
                                                      count=self.acq_freq_sweep_cnt,)
        #-------------------------Experiment-specific setup ends here--------------------------#
        
        #-------------------------below is some universal setting------------------------------#
        # Indentation in the descriptor is important, please do not change it.
        # Copy and paste does not preserve indentation in many cases.
        descriptor_shfqc = """ 
        instruments:
          SHFQC:
          - address: DEV12296
            uid: device_shfqc

        connections:
          device_shfqc:
            - iq_signal: q0/drive_line
              ports: SGCHANNELS/0/OUTPUT
            - iq_signal: q0/measure_line
              ports: [QACHANNELS/0/OUTPUT]
            - acquire_signal: q0/acquire_line
              ports: [QACHANNELS/0/INPUT]
        """

        self.device_setup = DeviceSetup.from_descriptor(
            descriptor_shfqc,
            server_host="127.0.0.1",
            server_port="8004",
            setup_name="UCLA_SHFQC",
        )
        self.emulate = True,
        self.session = Session(device_setup=self.device_setup)
        self.session.connect(do_emulation=self.emulate)
        #-----------------------------universal settings ends here-------------------------------#

        #-----------------------------Below is the SIGNAL MAP------------------------------------#
        self.map_q0 = {}
        self.map_q0['measure'] = self.device_setup.logical_signal_groups['q0'].logical_signals['measure_line']
        self.map_q0['acquire'] = self.device_setup.logical_signal_groups['q0'].logical_signals['acquire_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", amplitude=0.15, length=self.integration_length)
        #-----------------------------Pulse setup ends here--------------------------------------#

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
                        ):
        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
            ],
        )

        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp.sweep(uid='acq_freq_sweep', parameter=acq_freq_sweep):
                with exp.section(uid="spectroscopy"):
                    exp.play(signal='measure', pulse=self.readout_pulse,)
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
                # with exp.section(uid='relax'):
                #     exp.delay(signal='measure', time=self.integration_length)
                #     exp.reserve(signal='acquire')
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_freq_sweep,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-30,
            amplitude=0.1,
        )
        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=12,
                                                  acq_freq_sweep=self.acq_freq_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.compiled_exp_instance
