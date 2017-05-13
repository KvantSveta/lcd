import time
import signal
from datetime import date
from threading import Event
from threading import Thread
from subprocess import check_output

import RPi.GPIO as GPIO

from lcd import LCD

__author__ = "Evgeny Goncharov"

run_service = Event()
run_service.set()

ir_button_event = Event()


def handler(signum, frame):
    run_service.clear()


signal.signal(signal.SIGTERM, handler)

# LCD Address
ADDRESS = 0x3F

# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2C_BUS = 1

lcd = LCD(address=ADDRESS, port=I2C_BUS)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# IR sensor
IR_BUTTON = 4

GPIO.setup(IR_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def button_pressed(run_service, ir_button_event, IR_BUTTON):
    while run_service.is_set():
        if GPIO.input(IR_BUTTON):
            ir_button_event.set()

        time.sleep(.5)


Thread(
    target=button_pressed,
    args=(run_service, ir_button_event, IR_BUTTON)
).start()

while run_service.is_set():
    while not ir_button_event.is_set():
        time.sleep(.5)

    ir_button_event.clear()

    # '10 May 17'
    now_day = date.today().strftime("%e %b %y")

    error = 0
    critical = 0

    with open('/home/jd/Weather/weather.log') as f:
        data = f.readline()
        while data:
            if now_day in data:
                if 'ERROR' in data:
                    error += 1
                elif 'CRITICAL' in data:
                    critical += 1
            data = f.readline()

    lcd.lcd_show(
        first_row="Error: {}".format(error),
        second_row="Critical: {}".format(critical)
    )

    while not ir_button_event.is_set():
        time.sleep(.5)

    ir_button_event.clear()

    while not ir_button_event.is_set():
        output = check_output(
            [
                'docker',
                'ps',
                '-a',
                '--filter',
                'status=exited',
                '--format',
                '{{.ID}} {{.Names}}'
            ]
        )
        output = output.decode()
        output = output.split('\n')[:-1]

        lcd.lcd_show(first_row="Exited: {}".format(len(output)))

        time.sleep(5)

        for data in output:
            container_id, container_name = data.split()

            lcd.lcd_show(
                first_row="ID: {}".format(container_id),
                second_row="{}".format(container_name)
            )

            time.sleep(5)

GPIO.cleanup(IR_BUTTON)

# Реле для управления питанием дисплея
