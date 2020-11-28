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


class SpikePrimeDevice(object):
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
        time.sleep_ms(500)
        uart_tx.value(1)

        fm.register(self.tx_pin_num, self.uart_tx_fpioa_num, force=True)
        fm.register(self.rx_pin_num, self.uart_rx_fpioa_num, force=True)

        self.uart = UART(self.uart_num, 2400, bits=8, parity=None, stop=1, timeout=10000, read_buf_len=4096)

        self.uart.write(b'\x00')
        self.uart.write(b'\x40\x3e\x81')
        self.uart.write(b'\x49\x07\x07\xb6')
        self.uart.write(b'\x52\x00\xc2\x01\x00\x6e')
        self.uart.write(b'\x5f\x00\x00\x00\x02\x00\x00\x00\x02\xa0')

        self.uart.write(b'\xa7\x00\x66\x6c\x6f\x61\x74\x5f\x61\x72\x72\x61\x79\x00\x00\x00\x00\x00\x0e')
        self.uart.write(b'\x9f\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xeb')
        self.uart.write(b'\x9f\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xe8')
        self.uart.write(b'\x9f\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xe9')
        self.uart.write(b'\x87\x04\x00\x7c')
        self.uart.write(b'\x8f\x05\x10\x00\x65')
        self.uart.write(b'\x97\x80\x04\x03\x02\x01\xec')
        time.sleep_ms(5)

        self.uart.write(b'\xa6\x00\x69\x6e\x74\x33\x32\x5f\x61\x72\x72\x61\x79\x00\x00\x00\x00\x00\x0d')
        self.uart.write(b'\x9e\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xea')
        self.uart.write(b'\x9e\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xe9')
        self.uart.write(b'\x9e\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xe8')
        self.uart.write(b'\x86\x04\x00\x7d')
        self.uart.write(b'\x8e\x05\x10\x00\x64')
        self.uart.write(b'\x96\x80\x04\x02\x03\x00\xec')
        time.sleep_ms(5)

        self.uart.write(b'\xa5\x00\x69\x6e\x74\x31\x36\x5f\x61\x72\x72\x61\x79\x00\x00\x00\x00\x00\x08')
        self.uart.write(b'\x9d\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xe9')
        self.uart.write(b'\x9d\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xea')
        self.uart.write(b'\x9d\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xeb')
        self.uart.write(b'\x85\x04\x00\x7e')
        self.uart.write(b'\x8d\x05\x10\x00\x67')
        self.uart.write(b'\x95\x80\x04\x01\x03\x00\xec')
        time.sleep_ms(5)

        self.uart.write(b'\xa4\x00\x69\x6e\x74\x38\x5f\x61\x72\x72\x61\x79\x00\x00\x00\x00\x00\x00\x36')
        self.uart.write(b'\x9c\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xe8')
        self.uart.write(b'\x9c\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xeb')
        self.uart.write(b'\x9c\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xea')
        self.uart.write(b'\x84\x04\x00\x7f')
        self.uart.write(b'\x8c\x05\x10\x00\x66')
        self.uart.write(b'\x94\x80\x04\x00\x03\x00\xec')
        time.sleep_ms(5)

        self.uart.write(b'\x9b\x00\x66\x6c\x6f\x61\x74\x00\x00\x00\x14')
        self.uart.write(b'\x9b\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xef')
        self.uart.write(b'\x9b\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xec')
        self.uart.write(b'\x9b\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xed')
        self.uart.write(b'\x83\x04\x00\x78')
        self.uart.write(b'\x8b\x05\x10\x00\x61')
        self.uart.write(b'\x93\x80\x01\x03\x02\x01\xed')
        time.sleep_ms(5)

        self.uart.write(b'\x9a\x00\x69\x6e\x74\x33\x32\x00\x00\x00\x17')
        self.uart.write(b'\x9a\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xee')
        self.uart.write(b'\x9a\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xed')
        self.uart.write(b'\x9a\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xec')
        self.uart.write(b'\x82\x04\x00\x79')
        self.uart.write(b'\x8a\x05\x10\x00\x60')
        self.uart.write(b'\x92\x80\x01\x02\x03\x00\xed')
        time.sleep_ms(5)

        self.uart.write(b'\x99\x00\x69\x6e\x74\x31\x36\x00\x00\x00\x12')
        self.uart.write(b'\x99\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xed')
        self.uart.write(b'\x99\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xee')
        self.uart.write(b'\x99\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xef')
        self.uart.write(b'\x81\x04\x00\x7a')
        self.uart.write(b'\x89\x05\x10\x00\x63')
        self.uart.write(b'\x91\x80\x01\x01\x03\x00\xed')
        time.sleep_ms(5)

        self.uart.write(b'\x90\x00\x69\x6e\x74\x38\x24')
        self.uart.write(b'\x98\x01\x00\x00\x00\x00\x00\x00\xc8\x42\xec')
        self.uart.write(b'\x98\x02\x00\x00\x00\x00\x00\x00\xc8\x42\xef')
        self.uart.write(b'\x98\x03\x00\x00\x00\x00\x00\x00\xc8\x42\xee')
        self.uart.write(b'\x80\x04\x00\x7b')
        self.uart.write(b'\x88\x05\x10\x00\x62')
        self.uart.write(b'\x90\x80\x01\x00\x03\x00\xed')
        time.sleep_ms(5)

        self.uart.write(b'\x04')
        time.sleep_ms(5)

        print("waiting for ACK...")
        self.connected = self._wait_for_value(b'\x04')

        if self.connected:
            print("connected")
            self.uart.deinit()

            fm.register(self.tx_pin_num, self.tx_fpioa_gpio, force=True)
            uart_tx = GPIO(self.tx_gpio, GPIO.OUT)

            uart_tx.value(0)
            time.sleep_ms(10)

            fm.register(self.tx_pin_num, self.uart_tx_fpioa_num, force=True)
            fm.register(self.rx_pin_num, self.uart_rx_fpioa_num, force=True)

            self.uart = UART(self.uart_num, 115200, bits=8, parity=None, stop=1, timeout=10000, read_buf_len=4096)
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
        value = data & 0xFF
        payload = bytes([0xC0, value, self._get_checksum([0xC0, value])])
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
                zero = self.uart.readchar()
                b9 = self.uart.readchar()
                if zero == 0 and b9 == 0xb9:
                    size_mode = self.uart.readchar()
                    size = 2 ** ((size_mode & 0b111000) >> 3)
                    mode = size_mode & 0b111
                    checksum = self._get_checksum([x, zero, b9, size_mode])
                    for i in range(len(self.textBuffer)):
                        self.textBuffer[i] = ord(b' ')

                    for i in range(size):
                        self.textBuffer[i] = self.uart.readchar()
                        checksum ^= self.textBuffer[i]

                    expected_checksum = self.uart.readchar()
                    if expected_checksum == checksum:
                        print(self.textBuffer)
            elif x == 0x4C:
                thing = self.uart.readchar()
                checksum = self.uart.readchar()
                if checksum == self._get_checksum([x, thing]):
                    pass
            else:
                print(x)

        size = self._send_value(self.data)
        if not size:
            self.connected = False
