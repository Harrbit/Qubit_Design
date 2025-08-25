from laboneq.simple import *
import matplotlib.pyplot as plt
import numpy as np
import laboneq



class CavityCharacterization:
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
            - iq_signal: q0/cav_line
              ports: [QACHANNELS/2/OUTPUT]
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
        self.map_q0['cavity'] = self.device_setup.logical_signal_groups['q0'].logical_signals['cav_line']
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

                with exp.section(uid='initial_excitation'):
                    exp.play(signal='drive', pulse=self.x90_pulse)

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