#!/bin/env python
# -*- coding: utf8 -*-
# #########################################################################
# Spectro v0.6
#   Olivier Boesch (c) 2010-2022
#   Secomam s250 and Prim Spectrometers driver File - asynchronous version with threads
# #########################################################################

# Backend Code ####################################
import struct
from threading import Thread
from queue import Queue, Empty
from kivy.utils import platform
from kivy.logger import Logger

if platform in ['windows', 'linux']:
    import serial
    from serial import SerialException, SerialTimeoutException
elif platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
    from serial import SerialException

__author__ = "Olivier Boesch"
__version__ = "0.6 - 02/2022"

# Commands
Cmd_Prefix = b'\x1B'
Cmd_Init = b'\x5A'
Ans_Init_Ok = b'\x4F'
Ans_Init_Nok = b'\x4E'
Cmd_Firmware = b'\x22'
Cmd_Autotest = b'\x33'
Ans_Autotest_Ok = b'\x00'
Cmd_SetAbsWavelength = b'\x31'
Ans_SetAbsWavelength_Ok = b'\x1B'
Cmd_GetZeroAbs = b'\x30'
Ans_GetZeroAbs_Ok = b'\x54'
Cmd_GetAbs = b'\x32'
Ans_GetAbs_Ok = b'\x54'
Cmd_GetAbsData = b'\x45'
Cmd_BaseLine = b'\x34'
Ans_Baseline_Ok = b'\x1B'
Cmd_GetSpectrum = b'\x35'
Cmd_GetType = b'\x51'
Cmd_Stop = b'\xE7'

# Spectrometer types
Secoman_Models = {b'T\x00': 'S250 I+/E+', b'T\x01': 'S250 T+', b'P\x02': 'Prim Advanced', b'P\x01': 'Prim Lignt'}

# prefix, command, n_data, callback, timeout, callback_progress


class CommandThread(Thread):
    def __init__(self, spectro, cmd_queue: Queue):
        super().__init__()
        self.name = "Command_Thread"
        self.spectro = spectro
        self.command_queue = cmd_queue
        self.stop = False

    def run(self) -> None:
        Logger.info("S250: Starting command thread")
        while not self.stop:
            try:
                cmd_details = self.command_queue.get(block=True, timeout=1)
                Logger.info("S250 Thread: getting command {!r}".format(str(cmd_details)))
                self.treat_command(cmd_details)
            except Empty:
                Logger.debug("S250 Thread: timeout !")
        Logger.info("S250: Thread about to stop")

    def treat_command(self, command_details):
        return_value = None
        if not self.spectro.connected:
            return
        prefix, command, payload, n_data, callback, timeout, callback_progress = command_details
        self.spectro.conn.flush()
        self.spectro.send(prefix + command + payload)
        data = self.spectro.receive(n_data, timeout)
        if len(data) != n_data:
            return_value = None
        else:
            cmd_sent = command
            # start and check init spectrometer
            if cmd_sent == Cmd_Init:
                if data == Ans_Init_Ok:
                    return_value = True
                elif data == Ans_Init_Nok:
                    return_value = False
                else:
                    return_value = None
            # ask for firmware version
            elif cmd_sent == Cmd_Firmware:
                s = struct.unpack(">xB", data)[0]
                return_value = s
            # perform autotest
            elif cmd_sent == Cmd_Autotest:
                return_value = data == Ans_Autotest_Ok, int.from_bytes(data, 'big')
            # set wavelength for absorbance and kinetics
            elif cmd_sent == Cmd_SetAbsWavelength:
                return_value = data == Ans_SetAbsWavelength_Ok
            # get zero of absorbance value
            elif cmd_sent == Cmd_GetZeroAbs:
                if data == Ans_GetZeroAbs_Ok:
                    self.spectro.send(Cmd_GetAbsData)
                    abs = self.spectro.receive(3, 2.0)
                    return_value = struct.unpack(">Bh", abs)[1] / 10_000.0
            # get absorbance value
            elif cmd_sent == Cmd_GetAbs:
                if data == Ans_GetAbs_Ok:
                    self.spectro.send(Cmd_GetAbsData)
                    abs = self.spectro.receive(3, 2.0)
                    return_value = struct.unpack(">Bh", abs)[1] / 10_000.0
            # perform spectrum baseline
            elif cmd_sent == Cmd_BaseLine:
                return_value = data == Ans_Baseline_Ok
            # get spectrum data
            elif cmd_sent == Cmd_GetSpectrum:
                wlStart, N = struct.unpack(">xxHHx", data)
                spectrum_data = []
                spectrum_wl = []
                for i in range(N):
                    data = self.spectro.receive(2, self.timeout)
                    val = struct.unpack(">h", data)[0] / 10000.
                    wl = wlStart + i
                    spectrum_data.append(val)
                    spectrum_wl.append(wl)
                    if self.callback_progress is not None:
                        self.callback_progress((round(i/N*100), wl, val))
                return_value = spectrum_wl, spectrum_data
            # get type and model of spectrometer
            elif cmd_sent == Cmd_GetType:
                data = struct.unpack("2s", data)
                rawmodel = data[0]
                stringmodel = "Secomam " + Secoman_Models.get(rawmodel, default="")
                return_value = stringmodel, rawmodel
            # everything else (like stop)
            else:
                return_value = None
        if callback is not None:
            callback(return_value)


class S250Prim:
    waveLengthLimits = {'start': 330, 'end': 900, 'step': 3, 'speed': [1, 2, 3, 4, 5, 6, 7, 8]}
    serialComParameters = {'baudrate': 4800, 'bytesize': 8, 'parity': 'N',
                           'stopbits': 1}
    device_capabilities = {'serialcomparameters': serialComParameters, 'device': waveLengthLimits}
    connected = False
    zero_data = 0.
    spectrum_data = None
    spectrum_data_idx = None
    conn = None
    command_queue = Queue()
    command_thread = None

    def __init__(self, activity_out_clbk=None, activity_in_clbk=None):
        self.activity_in_clbk = activity_in_clbk
        self.activity_out_clbk = activity_out_clbk
        self.command_thread = CommandThread(self, self.command_queue)

    def __del__(self):
        self.stop = True
        self.command_thread.join()

    def send(self, s):
        if self.connected:
            if self.activity_out_clbk is not None:
                self.activity_out_clbk()
            Logger.debug("Serial: command sent {!r}".format(s))
            n = self.conn.write(s)
            return n

    def receive(self, n, timeout=0):
        if self.connected:
            self.conn.timeout = timeout
            c = self.conn.read(n)
            if c and self.activity_in_clbk is not None:
                self.activity_in_clbk()
            Logger.debug("Serial: data received {!r}".format(c))
            return c

    def thread_send(self, prefix=b'', command=b'', payload=b'', n=0, clbk=None, timeout=5, progress_clbk=None):
        command_details = prefix, command, payload, n, clbk, timeout, progress_clbk
        self.command_queue.put(command_details)

    def connect(self, port):
        try:
            if platform in ['windows', 'linux']:
                self.conn = serial.Serial(port, baudrate=self.serialComParameters['baudrate'],
                                          parity=self.serialComParameters['parity'],
                                          stopbits=self.serialComParameters['stopbits'])
            elif platform == 'android':
                device = usb.get_usb_device(port)
                if not device:
                    raise SerialException(
                        "No device {}".format(port)
                    )
                if not usb.has_usb_permission(device):
                    usb.request_usb_permission(device)
                    return False
                self.conn = serial4a.get_serial_port(
                    port,
                    self.serialComParameters['baudrate'],
                    8,
                    self.serialComParameters['parity'],
                    self.serialComParameters['stopbits'],
                    timeout=1
                )
            self.connected = True
            self.command_thread.start()
            return True
        except SerialException:
            self.command_thread.stop = True
            self.command_thread.join()
            self.connected = False
            return False

    def disconnect(self):
        try:
            self.command_thread.stop = True
            self.command_thread.join()
            self.conn.close()
        except SerialException:
            pass
        del self.conn
        self.conn = None
        self.connected = False

    def start_device(self, clbk=None):
        """ start_device : start spectrometer and test if initialization of spectrometer is completed - no arguments"""
        self.thread_send(command=Cmd_Init, n=1, clbk=clbk)

    def stop_device(self):
        """stop_device : stop spectrometer - no arguments"""
        self.thread_send(prefix=Cmd_Prefix, command=Cmd_Stop, n=0, clbk=None)

    def is_device_ready(self, clbk=None):
        """ is_device_ready : test if device is up and ready - no arguments"""
        self.thread_send(command=Cmd_Init, n=1, clbk=clbk)

    def get_firmware_version(self, clbk=None):
        """ get_firmware_version : get and return Prom version - no arguments"""
        self.thread_send(prefix=Cmd_Prefix, command=Cmd_Firmware, n=2, clbk=clbk)

    def get_model_name(self, clbk=None):
        """ get_model_name : return complete model name - no arguments"""
        self.thread_send(prefix=Cmd_Prefix, command=Cmd_GetType, n=2, clbk=clbk)

    def perform_autotest(self, clbk=None):
        """ perform_autotest : performs AutoTest of spectrometer - no arguments"""
        self.thread_send(prefix=Cmd_Prefix, command=Cmd_Autotest, n=1, clbk=clbk)

    def set_abs_wavelength(self, wl, gain=255, clbk=None):
        """ set_abs_wavelength : Set value of wavelength - [wl in nm] [gain from 0 to 255]"""
        self.conn.flush()
        data = struct.pack(">HxxB", wl, gain)
        self._thread_send(prefix=Cmd_Prefix, command=Cmd_SetAbsWavelength, payload=data, n=1, clbk=clbk)

    def get_abs_zero(self, clbk=None):
        """ get_abs_zero : get value of absorbance zero - no arguments"""
        self.thread_send(Cmd_Prefix + Cmd_GetZeroAbs, 1, clbk)

    def get_abs(self, clbk=None):
        """ get_abs : get value of absorbance - no arguments"""
        self.thread_send(Cmd_Prefix + Cmd_GetAbs, 1, clbk)

    def make_spectrum_baseline(self, wllo, wlhi, speed=8, res=3, clbk=None):
        """ make_spectrum_baseline : performs baseline of spectrum
                                     [wlLo in nm] [wlHi in nm] [speed from 1 to 8] [res = 3]"""
        data = struct.pack(">HHBBxx", wllo, wlhi, res, speed)
        self.send(Cmd_Prefix + Cmd_BaseLine + data, 1, clbk)

    def get_spectrum(self, clbk=None):
        """ get_spectrum_header : Gets and returns spectrum header - no arguments"""
        self.conn.flush()
        self.thread_send(Cmd_Prefix + Cmd_GetSpectrum, 7, clbk)
