# Copyright 2020 Isao Sonobe
# Copyright 2019-2020 ksasao <https://github.com/ksasao/brownie>
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

import audio
import gc
import image
import lcd
import sensor
import sys
import time
import uos
import os
from fpioa_manager import *
from machine import I2C
from Maix import I2S, GPIO
import KPU as kpu
import math
from LPF2 import SpikePrimeDevice


IMAGES_DIR = "/sd/images"
STARTUP_IMAGE = "/sd/startup.jpg"
CAMERA_MODE_IMAGE = "/sd/camera.jpg"
SHUTTER_SOUND = "/sd/kacha.wav"
FEATURE_MODEL = "/sd/model/mbnet751_feature.kmodel"
MAX_CLASS = 10
SIMILARITY_THRESHOLD = 0.3


lcd.init()
lcd.rotation(2)

try:
    from pmu import axp192
    pmu = axp192()
    pmu.enablePMICSleepMode(True)
except:
    pass

fm.register(board_info.SPK_SD, fm.fpioa.GPIO0)
spk_sd = GPIO(GPIO.GPIO0, GPIO.OUT)
spk_sd.value(1) #Enable the SPK output

fm.register(board_info.SPK_DIN, fm.fpioa.I2S0_OUT_D1)
fm.register(board_info.SPK_BCLK, fm.fpioa.I2S0_SCLK)
fm.register(board_info.SPK_LRCLK, fm.fpioa.I2S0_WS)
wav_dev = I2S(I2S.DEVICE_0)

fm.register(board_info.BUTTON_A, fm.fpioa.GPIO1)
but_a=GPIO(GPIO.GPIO1, GPIO.IN, GPIO.PULL_UP) #PULL_UP is required here!

fm.register(board_info.BUTTON_B, fm.fpioa.GPIO2)
but_b = GPIO(GPIO.GPIO2, GPIO.IN, GPIO.PULL_UP) #PULL_UP is required here!


def show_message(message, x=100, y=4, font_color=lcd.WHITE, bg_color=lcd.RED):
    lcd.draw_string(lcd.width() // 2 - x, lcd.height() // 2 - y, message, font_color, bg_color)

def show_image_file(filename):
    try:
        img = image.Image(filename)
        lcd.display(img)
    except:
        show_message("Error: Cannot find " + filename)

def play_sound(filename):
    try:
        player = audio.Audio(path=filename)
        player.volume(20)
        wav_info = player.play_process(wav_dev)
        wav_dev.channel_config(wav_dev.CHANNEL_1, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT, align_mode=I2S.STANDARD_MODE)
        wav_dev.set_sample_rate(wav_info[1])
        spk_sd.value(1)
        while True:
            ret = player.play()
            if ret is None or ret == 0:
                break
        player.finish()
        spk_sd.value(0)
    except:
        pass

def initialize_camera():
    err_counter = 0
    while True:
        try:
            sensor.reset() #Reset sensor may failed, let's try some times
            break
        except:
            err_counter = err_counter + 1
            if err_counter == 20:
                show_message("Error: Sensor Init Failed")
            time.sleep(0.1)
            continue

    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)  # QVGA=320x240
    sensor.set_windowing((224, 224))
    sensor.run(1)

def get_feature(task, img):
    feature = kpu.forward(task, img)
    return feature

def quantize_vector(vec):
    mx = max([abs(x) for x in vec])

    l = 0.0
    qvec = []
    for x in vec:
        qx = int(x / mx * 127 + 127)
        px = qx - 127
        l += px * px
        qvec.append(qx)

    l = math.sqrt(l)

    return l, bytearray(qvec)

def get_cos_distance(l1, qvec1, l2, qvec2):
    prod = 0.0
    for x1, x2 in zip(qvec1, qvec2):
        prod += (x1 - 127) * (x2 - 127)
    prod = prod / l1 / l2

    return 1 - prod  # 計算誤差のため、時々0.0を下回ったり2.0を超えたりします。
    #return min(1, max(0, 1 - prod))

if "sd" not in os.listdir("/"):
    show_message("Error: Cannot read SD Card", x=96)

try:
    os.mkdir(IMAGES_DIR)
except Exception as e:
    pass

show_image_file(STARTUP_IMAGE)
time.sleep(2)

if but_b.value() == 0:
    show_image_file(CAMERA_MODE_IMAGE)
    time.sleep(2)

    initialize_camera()

    currentImage = 1

    isButtonPressedA = 1
    isButtonPressedB = 1

    try:
        while(True):
            img = sensor.snapshot()

            if but_a.value() == 0 and isButtonPressedA == 0:
                try:
                    print(img)
                    img.save(IMAGES_DIR + "/" + str(currentImage) + ".jpg", roi=(0, 0, 224, 224), quality=95)
                    play_sound(SHUTTER_SOUND)
                except:
                    show_message("Error: Cannot Write to SD Card", x=124)
                    time.sleep(1)

                isButtonPressedA = 1

            if but_a.value() == 1:
                isButtonPressedA = 0

            if but_b.value() == 0 and isButtonPressedB == 0:
                currentImage = currentImage + 1
                if currentImage > MAX_CLASS:
                    currentImage = 1

                isButtonPressedB = 1

            if but_b.value() == 1:
                isButtonPressedB = 0

            img.draw_rectangle(0, 60, 320, 1, color=(0, 144, 255), thickness=10)
            img.draw_string(50, 55, "Class:%d" % (currentImage,), color=(255, 255, 255), scale=1)
            lcd.display(img)

    except KeyboardInterrupt:
        sys.exit()

else:
    should_connect_spike_prime = but_a.value() != 0

    initialize_camera()

    task = kpu.load(FEATURE_MODEL)
    info = kpu.netinfo(task)

    feature_list = []

    try:
        files = uos.listdir(IMAGES_DIR)
        for class_num in range(1, MAX_CLASS + 1):
            img_file = str(class_num) + ".jpg"
            if img_file in files:
                img = image.Image(IMAGES_DIR + "/" + img_file, copy_to_fb=True)
                img.draw_rectangle(0, 60, 320, 1, color=(0, 144, 255), thickness=10)
                img.draw_string(50, 55, "Class:%d" % (class_num,), color=(255, 255, 255), scale=1)
                lcd.display(img)
                img.pix_to_ai()
                #print(img)
                feature = get_feature(task, img)
                del img
                l, qvec = quantize_vector(feature[:])
                feature_list.append((l, qvec, class_num))
                gc.collect()
                kpu.fmap_free(feature)

        lcd.clear()

        for l1, qvec1, class_num in feature_list:
            similarities = ""
            for l2, qvec2, _ in feature_list:
                dist = get_cos_distance(l1, qvec1, l2, qvec2)
                similarities += "%0.2f  " % (dist,)
            print(class_num, similarities)

        sp_device = None
        if should_connect_spike_prime:
            show_message("Connecting to LPF2 Hub...", x=100, bg_color=lcd.BLACK)
            sp_device = SpikePrimeDevice(tx_pin=34, rx_pin=35)
            sp_device.initialize()

            while True:
                if sp_device.connected:
                    break
                sp_device.initialize()
                time.sleep_ms(100)

        while True:
            img = sensor.snapshot()

            current_feature = get_feature(task, img)
            current_l, current_qvec = quantize_vector(current_feature[:])
            similar_class = 0
            min_dist = 10.0
            kpu.fmap_free(current_feature)
            for l, qvec, class_num in feature_list:
                dist = get_cos_distance(l, qvec, current_l, current_qvec)
                if dist <= SIMILARITY_THRESHOLD and dist < min_dist:
                    similar_class = class_num
                    min_dist = dist

            if sp_device is not None:
                sp_device.set_data(similar_class)

            if similar_class > 0:
                img.draw_rectangle(0, 60, 320, 1, color=(0, 144, 255), thickness=10)
                img.draw_string(50, 55, "Class:%d" % (similar_class,), color=(255, 255, 255), scale=1)

            lcd.display(img)

    except KeyboardInterrupt:
        kpu.deinit(task)
        sys.exit()
