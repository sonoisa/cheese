# Copyright 2020 Isao Sonobe
# Copyright 2020 Tufts Center for Engineering Education and Outreach, Tufts University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from machine import UART, Timer
from fpioa_manager import fm
from Maix import GPIO
import time


class MindstromsDevice(object):
    def __init__(self, tx_pin, rx_pin, timer=Timer.TIMER0, timer_channel=Timer.CHANNEL0,
            tx_gpio=GPIO.GPIO1, tx_fpioa_gpio=fm.fpioa.GPIO1, uart_num=UART.UART2):

        self.connected = False
        self.uart = None
        self.tx_pin_num = tx_pin
        self.rx_pin_num = rx_pin
        self.data = 0
        self.current_mode = 0
        self.textBuffer = bytearray(b'             ')
        self.timer_num = timer
        self.timer_channel_num = timer_channel
        self.timer = None
        self.tx_gpio = tx_gpio
        self.tx_fpioa_gpio = tx_fpioa_gpio
        self.uart_num = uart_num
        if uart_num == UART.UART2:
            self.uart_tx_fpioa_num = fm.fpioa.UART2_TX
            self.uart_rx_fpioa_num = fm.fpioa.UART2_RX
        elif uart_num == UART.UART1:
            self.uart_tx_fpioa_num = fm.fpioa.UART1_TX
            self.uart_rx_fpioa_num = fm.fpioa.UART1_RX

    def initialize(self):
        assert not self.connected

        print("connecting...")

        fm.register(self.tx_pin_num, self.tx_fpioa_gpio, force=True)
        uart_tx = GPIO(self.tx_gpio, GPIO.OUT)

        uart_tx.value(0)
        time.sleep_ms(410)
        uart_tx.value(1)

        fm.register(self.tx_pin_num, self.uart_tx_fpioa_num, force=True)
        fm.register(self.rx_pin_num, self.uart_rx_fpioa_num, force=True)

        self.uart = UART(self.uart_num, 115200, bits=8, parity=None, stop=1, timeout=10000, read_buf_len=4096)

        # wait for \x52\x00\xc2\x01\x00\x6e
        self.uart.write(b'\x04')  # ACK?
        time.sleep_ms(10)
        self.uart.write(b'\x40\x3e\x81')  # CMD_TYPE(1), TypeID:0x3e, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x51\x07\x06\x08\x00\xa7')  # CMD_MODES(4), 8 modes for EV3, 7 views for EV3, 9 modes, 0 views, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x52\x00\xc2\x01\x00\x6e')  # CMD_SPEED(4), speed:115200, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x5f\x00\x00\x00\x10\x00\x00\x00\x10\xa0')  # CMD_VERSION(8), fw-version:1.0.00.0000, hw-version:1.0.00.0000, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa0\x20\x43\x41\x4c\x49\x42\x00\x40\x40\x00\x00\x04\x84\x00\x00\x00\x00\xba')  # INFO_NAME(16) | mode:0+8, "CALIB\0" + flags(0x40, 0x40, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x98\x21\x00\x00\x00\x00\x00\x00\x7f\x43\x7a')  # INFO_RAW(8) | mode:0+8, min:0.0, max:255.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x98\x22\x00\x00\x00\x00\x00\x00\xc8\x42\xcf')  # INFO_PCT(8) | mode:0+8, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x98\x23\x00\x00\x00\x00\x00\x00\x7f\x43\x78')  # INFO_SI(8) | mode:0+8, min:0.0, max:255.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x90\x24\x50\x43\x54\x00\x0c')  # INFO_SYMBOL(4) | mode:0+8, "PCT\0", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x88\x25\x00\x00\x52')  # INFO_MAPPING(2) | mode:0+8, input:0, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x90\xa0\x07\x00\x03\x00\xcb')  # INFO_FORMAT(4) | mode:0+8, data-sets:7, format:0, figures:3, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa7\x00\x41\x44\x52\x41\x57\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\xd9')  # INFO_NAME(16) | mode:7, "ADRAW\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9f\x01\x00\x00\x00\x00\x00\x00\x80\x44\xa5')  # INFO_RAW(8) | mode:7, min:0.0, max:1024.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9f\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xe8')  # INFO_PCT(8) | mode:7, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9f\x03\x00\x00\x00\x00\x00\x00\x80\x44\xa7')  # INFO_SI(8) | mode:7, min:0.0, max:1024.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x97\x04\x50\x43\x54\x00\x2b')  # INFO_SYMBOL(4) | mode:7, "PCT\0", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8f\x05\x90\x00\xe5')  # INFO_MAPPING(2) | mode:7, input:0x90, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x97\x80\x01\x01\x04\x00\xec')  # INFO_FORMAT(4) | mode:7, data-sets:1, format:1, figures:4, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa6\x00\x50\x49\x4e\x47\x00\x00\x40\x80\x00\x00\x04\x84\x00\x00\x00\x00\x09')  # INFO_NAME(16) | mode:6, "PING\0\0" + flags(0x40, 0x80, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9e\x01\x00\x00\x00\x00\x00\x00\x80\x3f\xdf')  # INFO_RAW(8) | mode:6, min:0.0, max:1.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9e\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xe9')  # INFO_PCT(8) | mode:6, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9e\x03\x00\x00\x00\x00\x00\x00\x80\x3f\xdd')  # INFO_SI(8) | mode:6, min:0.0, max:1.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x96\x04\x50\x43\x54\x00\x2a')  # INFO_SYMBOL(4) | mode:6, "PCT\0", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8e\x05\x00\x90\xe4')  # INFO_MAPPING(2) | mode:6, input:0, output:0x90, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x96\x80\x01\x00\x01\x00\xe9')  # INFO_FORMAT(4) | mode:6, data-sets:1, format:0, figures:1, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa5\x00\x4c\x49\x47\x48\x54\x00\x40\x20\x00\x00\x04\x84\x00\x00\x00\x00\xe4')  # INFO_NAME(16) | mode:5, "LIGHT\0" + flags(0x40, 0x20, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9d\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xe9')  # INFO_RAW(8) | mode:5, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9d\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xea')  # INFO_PCT(8) | mode:5, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9d\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xeb')  # INFO_SI(8) | mode:5, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x95\x04\x50\x43\x54\x00\x29')  # INFO_SYMBOL(4) | mode:5, "PCT\0", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8d\x05\x00\x10\x67')  # INFO_MAPPING(2) | mode:5, input:0, output:0x10, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x95\x80\x04\x00\x03\x00\xed')  # INFO_FORMAT(4) | mode:5, data-sets:4, format:0, figures:3, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa4\x00\x54\x52\x41\x57\x00\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\x8b')  # INFO_NAME(16) | mode:4, "TRAW\0\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9c\x01\x00\x00\x00\x00\x00\xc4\x63\x46\x83')  # INFO_RAW(8) | mode:4, min:0.0, max:14577.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9c\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xeb')  # INFO_PCT(8) | mode:4, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9c\x03\x00\x00\x00\x00\x00\xc4\x63\x46\x81')  # INFO_SI(8) | mode:4, min:0.0, max:14577.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8c\x04\x75\x53\x51')  # INFO_SYMBOL(2) | mode:4, "uS", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8c\x05\x90\x00\xe6')  # INFO_MAPPING(2) | mode:4, input:0x90, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x94\x80\x01\x02\x05\x00\xed')  # INFO_FORMAT(4) | mode:4, data-sets:1, format:2, figures:5, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa3\x00\x4c\x49\x53\x54\x4e\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\xd0')  # INFO_NAME(16) | mode:3, "LISTN\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9b\x01\x00\x00\x00\x00\x00\x00\x80\x3f\xda')  # INFO_RAW(8) | mode:3, min:0.0, max:1.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9b\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xec')  # INFO_PCT(8) | mode:3, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9b\x03\x00\x00\x00\x00\x00\x00\x80\x3f\xd8')  # INFO_SI(8) | mode:3, min:0.0, max:1.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8b\x04\x53\x54\x77')  # INFO_SYMBOL(2) | mode:3, "ST", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8b\x05\x10\x00\x61')  # INFO_MAPPING(2) | mode:3, input:0x10, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x93\x80\x01\x00\x01\x00\xec')  # INFO_FORMAT(4) | mode:3, data-sets:1, format:0, figures:1, decimals:0, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa2\x00\x53\x49\x4e\x47\x4c\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\xc2')  # INFO_NAME(16) | mode:2, "SINGL\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x9a\x01\x00\x00\x00\x00\x00\x40\x1c\x45\x7d')  # INFO_RAW(8) | mode:2, min:0.0, max:2500.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9a\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xed')  # INFO_PCT(8) | mode:2, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x9a\x03\x00\x00\x00\x00\x00\x00\x7a\x43\x5f')  # INFO_SI(8) | mode:2, min:0.0, max:250.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8a\x04\x43\x4d\x7f')  # INFO_SYMBOL(2) | mode:2, "CM", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x8a\x05\x90\x00\xe0')  # INFO_MAPPING(2) | mode:2, input:0x00, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x92\x80\x01\x01\x05\x01\xe9')  # INFO_FORMAT(4) | mode:2, data-sets:1, format:1, figures:5, decimals:1, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa1\x00\x44\x49\x53\x54\x53\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\xc7')  # INFO_NAME(16) | mode:1, "DISTS\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x99\x01\x00\x00\x00\x00\x00\x00\xa0\x43\x84')  # INFO_RAW(8) | mode:1, min:0.0, max:320.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x99\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xee')  # INFO_PCT(8) | mode:1, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x99\x03\x00\x00\x00\x00\x00\x00\x00\x42\x27')  # INFO_SI(8) | mode:1, min:0.0, max:32.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x89\x04\x43\x4d\x7c')  # INFO_SYMBOL(2) | mode:1, "CM", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x89\x05\xf1\x00\x82')  # INFO_MAPPING(2) | mode:1, input:0xf1, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x91\x80\x01\x01\x04\x01\xeb')  # INFO_FORMAT(4) | mode:1, data-sets:1, format:1, figures:4, decimals:1, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa0\x00\x44\x49\x53\x54\x4c\x00\x40\x00\x00\x00\x04\x84\x00\x00\x00\x00\xd9')  # INFO_NAME(16) | mode:0, "DISTL\0" + flags(0x40, 0x00, 0x00, 0x00, 0x04, 0x84), checksum
        self.uart.write(b'\x98\x01\x00\x00\x00\x00\x00\x40\x1c\x45\x7f')  # INFO_RAW(8) | mode:0, min:0.0, max:2500.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x98\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xef')  # INFO_PCT(8) | mode:0, min:0.0, max:100.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x98\x03\x00\x00\x00\x00\x00\x00\x7a\x43\x5d')  # INFO_SI(8) | mode:0, min:0.0, max:250.0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x88\x04\x43\x4d\x7d')  # INFO_SYMBOL(2) | mode:0, "CM", checksum
        time.sleep_ms(1)
        self.uart.write(b'\x88\x05\x91\x00\xe3')  # INFO_MAPPING(2) | mode:0, input:0x91, output:0, checksum
        time.sleep_ms(1)
        self.uart.write(b'\x90\x80\x01\x01\x05\x01\xeb')  # INFO_FORMAT(4) | mode:0, data-sets:1, format:1, figures:5, decimals:1, checksum
        time.sleep_ms(18)

        self.uart.write(b'\xa0\x08\x00\x2d\x00\x33\x05\x47\x38\x33\x30\x31\x32\x36\x00\x00\x00\x00\x05')
        self.uart.write(b'\x04')

        print("waiting for ACK...")
        self.connected = self._wait_for_value(b'\x04')

        if self.connected:
            print("connected")
            self.set_data(0)
            self.timer = Timer(self.timer_num, self.timer_channel_num,
                mode=Timer.MODE_PERIODIC, period=200, callback=self._handle_message_callback)
            self.timer.start()
        else:
            print("not connected")

        return self.connected

    def _wait_for_value(self, expected_value, timeout=2):
        starttime = time.time()
        currenttime = starttime
        status = False
        #count = 0
        while (currenttime - starttime) < timeout:
            time.sleep_ms(5)
            #print(count)
            #count += 1
            currenttime = time.time()
            if self.uart.any() > 0:
                data = self.uart.readchar()
                #print(data)
                if data == ord(expected_value):
                    status = True
                    break
        return status

    def set_data(self, data):
        self.data = data

    def _get_checksum(self, values):
        checksum = 0xFF
        for x in values:
            checksum ^= x
        return checksum

    def _send_value(self, data):
        mode = self.current_mode  # 0:DISTL, 1:DISTS
        l_value = data & 0xFF
        h_value = (data >> 8) & 0xFF
        payload = bytes([0x46, 0x00, 0xB9, 0xC8 | mode, l_value, h_value, self._get_checksum([0xC8 | mode, l_value, h_value])])
        size = self.uart.write(payload)
        return size

    def _handle_message_callback(self, timer):
        if not self.connected:
            return

        while self.uart.any() > 0:
            x = self.uart.readchar()
            if x == 0:
                pass
            elif x == 0x02:
                pass
            elif x == 0x43:
                mode = self.uart.readchar()
                checksum = self.uart.readchar()
                if checksum == self._get_checksum([x, mode]):
                    self.current_mode = mode
            elif x == 0x46:
                zero_or_one = self.uart.readchar()
                b9_or_b8 = self.uart.readchar()
                if (zero_or_one == 0 and b9_or_b8 == 0xb9) or (zero_or_one == 1 and b9_or_b8 == 0xb8):
                    size_mode = self.uart.readchar()
                    size = 2 ** ((size_mode & 0b111000) >> 3)
                    mode = (size_mode & 0b111) + (zero_or_one << 3)
                    checksum = self._get_checksum([x, zero_or_one, b9_or_b8, size_mode])
                    for i in range(len(self.textBuffer)):
                        self.textBuffer[i] = ord(b' ')

                    for i in range(size):
                        self.textBuffer[i] = self.uart.readchar()
                        checksum ^= self.textBuffer[i]

                    expected_checksum = self.uart.readchar()
                    if expected_checksum == checksum:
                        print(self.textBuffer)
            elif x == 0x4C:
                # ex: 4C 20 00 93
                l_value = self.uart.readchar()
                h_value = self.uart.readchar()
                checksum = self.uart.readchar()
                if checksum == self._get_checksum([x, l_value, h_value]):
                    pass
            else:
                print(x)

        size = self._send_value(self.data)
        if not size:
            self.connected = False
