"""
BasicCharacterization.py

A collection of classes for basic qubit and resonator characterization experiments using Zurich Instruments LabOne Q framework.

Author: Runzhao Guo (郭润钊)
Copyright (c) 2025 Runzhao Guo. All rights reserved.
License: Personal and educational use only.

This module provides:
- Resonator spectroscopy (ResSpec)
- Amplitude sweep spectroscopy (PunchOut)
- Qubit spectroscopy (QuSpec)
- Two-tone spectroscopy (TwoToneSpec)

Dependencies:
    - laboneq
    - numpy
    - matplotlib

For documentation and examples for laboneq, see:
    https://docs.zhinst.com/labone_q_user_manual/
    https://github.com/zhinst/laboneq

"""


# README: all experiments are divided into 4 parts, init, setup, calibration, and run. 
# It is preferred to define signal configurations, i.e. frequency and amplitude, in calibration part and pulse configurations, i.e. waveform, in init part.


from laboneq.simple import *
import matplotlib.pyplot as plt
import numpy as np
import laboneq



class ResSpec:

    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9
        self.acq_freq_sweep_cnt = 2001
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
              ports: SGCHANNELS/1/OUTPUT
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
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         acq_freq_sweep = LinearSweepParameter(uid='acq_freq_sweep_default',
                                                                 start=-100e6,
                                                                 stop=100e6,
                                                                 count=2001),
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
                    exp.play(signal='measure', pulse=self.readout_pulse, amplitude=0.1)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
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
                                                  average_exponent=0,
                                                  acq_freq_sweep=self.acq_freq_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp


class PunchOut:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9
        self.acq_freq_sweep_cnt = 2001
        self.acq_freq_sweep_start = (self.acq_res_freq - 100e6) - self.acq_lo_freq
        self.acq_freq_sweep_stop = (self.acq_res_freq + 100e6) - self.acq_lo_freq
        
        self.acq_freq_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.acq_freq_sweep_start, 
                                                      stop=self.acq_freq_sweep_stop, 
                                                      count=self.acq_freq_sweep_cnt,)
        self.acq_amp_sweep = LinearSweepParameter(uid='acquisition_amplitude_sweep',
                                                  start=0.1,
                                                  stop=0.7,
                                                  count=11)
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
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         acq_freq_sweep = LinearSweepParameter(uid='acq_freq_sweep_default',
                                                                 start=-100e6,
                                                                 stop=100e6,
                                                                 count=2001),
                         acq_amp_sweep = 0.1,
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
                    exp.play(signal='measure', pulse=self.readout_pulse, amplitude=acq_amp_sweep)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_freq_sweep,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,
            amplitude=0.5623,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self, acq_amp_sweep=0.1):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  acq_freq_sweep=self.acq_freq_sweep,
                                                  acq_amp_sweep=acq_amp_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp


class QuSpec:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#
        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9
        self.qb_freq_sweep_cnt = 1001
        self.qb_freq_sweep_start = (self.qb_drv_freq - 100e6) - self.qb_lo_freq
        self.qb_freq_sweep_stop = (self.qb_drv_freq + 100e6) - self.qb_lo_freq
        
        # Spectroscopy sweep parameters
        self.qb_freq_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.qb_freq_sweep_start, 
                                                      stop=self.qb_freq_sweep_stop, 
                                                      count=self.qb_freq_sweep_cnt,)
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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        self.g_pulse = pulse_library.gaussian(uid="g_pulse", length=self.integration_length)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         qb_freq_sweep = LinearSweepParameter(uid='acq_freq_sweep_default',
                                                                 start=-100e6,
                                                                 stop=100e6,
                                                                 count=2001),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp.sweep(uid='qubit_freq_sweep', parameter=qb_freq_sweep):
                with exp.section(uid='qubit_excitation'):
                    exp.play(signal='drive', pulse=self.g_pulse)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')
                with exp.section(uid="spectroscopy"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_freq_sweep,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  qb_freq_sweep=self.qb_freq_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.compiled_exp_instance
    

class TwoToneSpec:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#

        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9

        # Spectroscopy sweep parameters
        self.qb_freq_sweep_cnt = 2001
        self.qb_freq_sweep_start = (self.qb_drv_freq - 100e6) - self.qb_lo_freq
        self.qb_freq_sweep_stop = (self.qb_drv_freq + 100e6) - self.qb_lo_freq
        
        self.qb_freq_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.qb_freq_sweep_start, 
                                                      stop=self.qb_freq_sweep_stop, 
                                                      count=self.qb_freq_sweep_cnt,)
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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         qb_freq_sweep = LinearSweepParameter(uid='acq_freq_sweep_default',
                                                                 start=-100e6,
                                                                 stop=100e6,
                                                                 count=2001),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp.sweep(uid='acq_freq_sweep', parameter=qb_freq_sweep):
                with exp.section(uid="spectroscopy"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.play(signal='drive', pulse=self.readout_pulse)  # This is the qubit drive pulse.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_freq_sweep,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  qb_freq_sweep=self.qb_freq_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp
    

class TimeRabi:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#

        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_drv_time = 50e-9
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9
        
        
        # Rabi Parameters and rabi sweep
        self.rabi_length_start = 300e-9
        self.rabi_length_stop = 1000e-9
        self.rabi_length_cnt = 10
        self.rabi_length_sweep = LinearSweepParameter(uid="rabi_length_sweep", 
                                                        start=self.rabi_length_start, 
                                                        stop=self.rabi_length_stop, 
                                                        count=self.rabi_length_cnt,)

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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        self.x180_pulse = pulse_library.const(uid="x180_pulse", length=50e-9)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         rabi_length_sweep = LinearSweepParameter(uid='rabi_length_sweep_default',
                                                                 start=1e-9,
                                                                 stop=100e-9,
                                                                 count=501),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            with exp.sweep(uid='rabi_length_sweep', parameter=rabi_length_sweep):
                with exp.section(uid='qubit_excitation'):
                    exp.play(signal='drive', pulse=self.x180_pulse, length=rabi_length_sweep)  # This is the qubit drive pulse.
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')

                with exp.section(uid="measurement"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
                    exp.reserve(signal='drive')

                with exp.section(uid="wait"):
                    exp.delay(signal="drive",time=100e-6)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_drv_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  rabi_length_sweep=self.rabi_length_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp
    

class AmplitudeRabi:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#

        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_drv_time = 50e-9
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9
        
        
        # Rabi Parameters and rabi sweep
        self.rabi_amp_start = 0.1
        self.rabi_amp_stop = 0.5
        self.rabi_amp_cnt = 501
        self.rabi_amp_sweep = LinearSweepParameter(uid="rabi_amp_sweep", 
                                                        start=self.rabi_amp_start, 
                                                        stop=self.rabi_amp_stop, 
                                                        count=self.rabi_amp_cnt,)

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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        self.x180_pulse = pulse_library.const(uid="x180_pulse", length=50e-9)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         rabi_amp_sweep = LinearSweepParameter(uid='rabi_amp_sweep_default',
                                                                 start=0.1,
                                                                 stop=0.5,
                                                                 count=501),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            with exp.sweep(uid='rabi_amp_sweep', parameter=rabi_amp_sweep):
                with exp.section(uid='qubit_excitation'):
                    exp.play(signal='drive', pulse=self.x180_pulse, amplitude=rabi_amp_sweep)  # This is the qubit drive pulse.
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')

                with exp.section(uid="measurement"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
                    exp.reserve(signal='drive')

                with exp.section(uid="wait"):
                    exp.delay(signal="drive",time=100e-6)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_drv_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  rabi_amp_sweep=self.rabi_amp_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp


class T1:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#

        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_drv_time = 50e-9
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9

        # Sweep parameters
        self.delay_sweep_cnt = 501
        self.delay_sweep_start = 1e-6
        self.delay_sweep_stop = 10e-6
        
        self.delay_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.delay_sweep_start, 
                                                      stop=self.delay_sweep_stop, 
                                                      count=self.delay_sweep_cnt,)
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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        self.x180_pulse = pulse_library.const(uid="x180_pulse", length=self.qb_drv_time)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         delay_sweep = LinearSweepParameter(uid='delay_sweep_default',
                                                                 start=1e-9,
                                                                 stop=100e-9,
                                                                 count=501),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            with exp.sweep(uid='acq_freq_sweep', parameter=delay_sweep):
                with exp.section(uid='qubit_excitation'):
                    exp.play(signal='drive', pulse=self.x180_pulse)  # This is the qubit drive pulse.
                    exp.delay(signal='drive',time=delay_sweep)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')

                with exp.section(uid="measurement"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
                    exp.reserve(signal='drive')

                with exp.section(uid="wait"):
                    exp.delay(signal="drive",time=100e-6)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_drv_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  rabi_delay_sweep=self.delay_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp
    

class Ramsey:
    def __init__ (self):
        print(laboneq.__version__)

        #-------------------------Below is some Experiment-specific setup---------------------#

        # readout setup
        self.integration_length = 1e-6
        self.acq_lo_freq = 7e9
        self.acq_res_freq = 7.10e9

        # Qubit drive setup
        self.qb_drv_time = 50e-9
        self.qb_lo_freq = 5e9
        self.qb_drv_freq = 5.10e9

        # Sweep parameters
        self.delay_sweep_cnt = 501
        self.delay_sweep_start = 0.1e-6
        self.delay_sweep_stop = 10e-6
        
        self.delay_sweep = LinearSweepParameter(uid="acquisition_frequency_sweep",
                                                      start=self.delay_sweep_start, 
                                                      stop=self.delay_sweep_stop, 
                                                      count=self.delay_sweep_cnt,)
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
              ports: SGCHANNELS/1/OUTPUT
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
        self.map_q0['drive'] = self.device_setup.logical_signal_groups['q0'].logical_signals['drive_line']
        #-----------------------------SIGNAL MAP ends here---------------------------------------#

        #-----------------------------Below is the pulse setup-----------------------------------#
        self.readout_pulse = pulse_library.const(uid="readout_pulse", length=self.integration_length)
        self.x90_pulse = pulse_library.const(uid="x90_pulse", length=self.qb_drv_time)
        #-----------------------------Pulse setup ends here--------------------------------------#

    def setup_experiment(self, 
                         exp_id='punch_out',
                         average_exponent = 2,
                         delay_sweep = LinearSweepParameter(uid='delay_sweep_default',
                                                                 start=1e-9,
                                                                 stop=100e-9,
                                                                 count=501),
                        ):

        exp = Experiment(
            uid = exp_id,
            signals = [
                ExperimentSignal("measure"),
                ExperimentSignal("acquire"),
                ExperimentSignal("drive"),
            ],
        )
        with exp.acquire_loop_rt(
            uid='freq_shots',
            count=pow(2, average_exponent),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            with exp.sweep(uid='acq_freq_sweep', parameter=delay_sweep):
                with exp.section(uid='qubit_excitation'):
                    exp.play(signal='drive', pulse=self.x90_pulse)  # This is the qubit drive pulse.
                    exp.delay(signal='drive',time=delay_sweep)
                    exp.play(signal='drive', pulse=self.x90_pulse)  # This is the qubit drive pulse.
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')

                with exp.section(uid="measurement"):
                    exp.play(signal='measure', pulse=self.readout_pulse)  # This is the readout pulse, amplitude is set to 0.1.
                    exp.acquire(signal='acquire', handle='res_spec', length=self.integration_length),  # incase people are wondering, yes, 'res_spec' stand for 'resonator spectroscopy'.
                    exp.reserve(signal='drive')

                with exp.section(uid="wait"):
                    exp.delay(signal="drive",time=100e-6)
                    exp.reserve(signal='measure')
                    exp.reserve(signal='acquire')
        return exp
    

    def calibrate_experiment(self):
        exp_calibration = Calibration()
        exp_calibration["measure"] = SignalCalibration(
            oscillator = Oscillator(uid = "qa_osc",  # let's just say here 'qa' stands for quantum analyzer
                                    frequency = self.acq_res_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator = Oscillator(uid="qa_lo",
                                          frequency=self.acq_lo_freq),
            range=-15,  # the ultimate goal is to get -90 dB at to sample, current attenuaion is 70 dB(Aug 24, 2025 cooldown), so we need -20 dB at the output of the AWG.
            amplitude=0.5623,  # HOWEVER, 1.0 amplitude causes overload at output, so we use 0.5623 instead, which is -5 dB, which explains why we have -15 dB here instead of -20 dB.
        )

        exp_calibration["drive"] = SignalCalibration(
            oscillator = Oscillator(uid='ch1_osc_0',
                                    frequency=self.qb_drv_freq,
                                    modulation_type=ModulationType.HARDWARE),
            local_oscillator=Oscillator(uid='ch1_lo', frequency=self.qb_lo_freq),
            range=-30,
            amplitude=1.0,
        )

        exp_calibration["acquire"] = SignalCalibration(
            range = -40,
            amplitude = 1.0,
        )
        return exp_calibration
        

    def run_experiment(self):
        self.exp_instance = self.setup_experiment(exp_id='punch_out',
                                                  average_exponent=0,
                                                  delay_sweep=self.delay_sweep,)
        self.exp_instance.set_signal_map(self.map_q0)
        self.exp_calibration = self.calibrate_experiment()
        self.exp_instance.set_calibration(self.exp_calibration)
        self.compiled_exp_instance = self.session.compile(self.exp_instance)
        self.run_exp = self.session.run(self.compiled_exp_instance)
        self.data_exp = self.run_exp.get_data('res_spec')
        self.freq_exp = self.run_exp.get_axis('res_spec')[0]

        return self.data_exp