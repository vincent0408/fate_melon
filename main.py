import cv2
import subprocess
import numpy as np
import time
from datetime import datetime
import ddddocr
from PIL import Image

def adb_shell_command(device_id, command):
    subprocess.check_output(f"adb -s {device_id} shell {command}", shell=True)

def get_screenshot(device_id):
    pipe = subprocess.Popen(f"adb -s {device_id} shell screencap -p",
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n')
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    return image

def portrait_pause_btn_exist(device_id):
    global pause_img
    image = get_screenshot(device_id)
    possible_pause = cv2.threshold(image[1411:1481, 420:490], 127, 255, cv2.THRESH_BINARY)[1]
    return (pause_img == possible_pause).all()

def resume_portrait_playing(device_id):
    while(True):
        if(portrait_pause_btn_exist(device_id)):
            adb_shell_command(device_id, "input tap 440 1450")
        else:
            adb_shell_command(device_id, "content insert --uri content://settings/system --bind name:s:user_rotation --bind value:i:2")
            print(f"Resumed {device_id}'s portrait playing! at {datetime.now()}")
            return 


def resume_landscape_playing(image, device_id):
    global pause_img
    adb_shell_command(device_id, "input tap 800 570")
    possible_pause = cv2.threshold(image[790:860, 770:840],127,255,cv2.THRESH_BINARY)[1]
    if((pause_img == possible_pause).all()):
        adb_shell_command(device_id, "input tap 800 828")
        print(f"Resumed {device_id} landscape playing! at {datetime.now()}")
    else:
        print(f"Nothing to resume for {device_id}'s landscape playing! at {datetime.now()}")

def verify_actions(device_id):
    global ocr
    image = get_screenshot(device_id)    
    if(image.shape == (900, 1600, 3)):
        resume_landscape_playing(image, device_id)
        return
    else:
        if(portrait_pause_btn_exist(device_id)):
            resume_portrait_playing(device_id)
            return
        else:
            for i in range(5):
                while(True):
                    guess = ocr.classification(Image.fromarray(image[275:375, 200:550]))
                    if(guess.isnumeric()):
                        break
                    else:
                        subprocess.check_output(f"adb -s {device_id} shell input tap 800 295", shell=True)
                        image = get_screenshot(device_id)    
                adb_shell_command(device_id, "input tap 500 550")
                adb_shell_command(device_id, "input text {guess}")
                adb_shell_command(device_id, "input tap 450 700")
                if(portrait_pause_btn_exist(device_id)):
                    resume_portrait_playing(device_id)
                    print(f"Bypassed {device_id}'s Captcha at {datetime.now()}")
                    return
                else:
                    print(f"Something is wrong when bypassing captcha for {device_id}, attempt {i+1}")
                    time.sleep(5)
            return


if __name__ == '__main__':
    print("Starting...")
    devices = subprocess.check_output("adb devices").decode("utf-8").replace('\r\n', '').replace('\tdevice', ' ').replace('List of devices attached', '').strip().split(' ')
    # pause_img_l = cv2.imread("pause_btn_l.png")
    # pause_img_p = cv2.imread("pause_btn_p.png")
    pause_img = cv2.imread("pause_btn.png")

    ocr = ddddocr.DdddOcr(show_ad=False)
    while(True):
        for device in devices:
            verify_actions(device)
        time.sleep(300)