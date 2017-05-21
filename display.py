import re
import signal
from datetime import date
from threading import Event
from subprocess import check_output

import RPi.GPIO as GPIO

from lcd import LCD

__author__ = "Evgeny Goncharov"

run_service = Event()
run_service.set()


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


def show_weather_log():
    # '10 May 17'
    now_day = date.today().strftime("%e %b %y")

    error = 0
    critical = 0

    # weather.log
    with open("/home/jd/Weather/weather.log") as f:
        data = f.readline()
        while data:
            if now_day in data:
                if "ERROR" in data:
                    error += 1
                elif "CRITICAL" in data:
                    critical += 1
            data = f.readline()

    lcd.lcd_show(
        first_row="Error: {}".format(error),
        second_row="Critical: {}".format(critical)
    )


def show_docker_ps():
    # docker
    output = check_output(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "status=exited",
            "--format",
            "{{.ID}} {{.Names}}"
        ]
    )
    output = output.decode()
    output = output.splitlines()

    lcd.lcd_show(
        first_row="Docker",
        second_row="Exited: {}".format(len(output))
    )

    for data in output:
        container_id, container_name = data.split()

        lcd.lcd_show(
            first_row="ID: {}".format(container_id),
            second_row="{}".format(container_name)
        )


def show_up_time():
    # up time, load average
    output = check_output(["uptime"])
    output = output.decode()
    output = output.strip()
    # '04:10:05 up 11 days, 21:29,  2 users,  load average: 0,10, 0,08, 0,06'
    output = re.split(",[ ]+\d user[s]?,[ ]+", output)
    # ['04:10:05 up 11 days, 21:29', 'load average: 0,10, 0,08, 0,06']

    up_time, load_average = output
    # 'up 11 days, 21:29'
    up_time = up_time[9:]

    if len(up_time) <= 16:
        lcd.lcd_show(
            first_row="Up time:",
            second_row="{}".format(up_time)
        )
    elif len(up_time) <= 32:
        lcd.lcd_show(
            first_row="{}".format(up_time[:16]),
            second_row="{}".format(up_time[16:])
        )
    else:
        lcd.lcd_show(
            first_row="Up time error:",
            second_row="A lot of letters"
        )

    # 1     5     15 minutes
    # load average: 0.00, 0.01, 0.03
    load_average = load_average.split(": ")

    lcd.lcd_show(
        first_row="Load average",
        second_row="{}".format(load_average[1])
    )


def show_free():
    # free -m
    #       total        used        free      shared  buff/cache   available
    # Mem:    925         156          62          48         706         645
    # total = used + buff/cache + free
    output = check_output(["free", "-m"])
    output = output.decode()
    output = output.splitlines()[1]
    memory = re.findall('\d{1,3}', output)

    lcd.lcd_show(
        first_row="All use b/c free",
        second_row="{0: <4}{1: <4}{2: <4}{3: <4}".format(
            memory[0], memory[1], memory[4], memory[2]
        )
    )


def show_df():
    # df
    output = check_output(["df", "-h"])
    output = output.decode()
    output = output.splitlines()

    for i in output:
        if "/dev/root" in i:
            # 'Filesystem      Size  Used Avail Use% Mounted on'
            # '/dev/root        15G  7,2G  7,5G  50% /'
            root = re.findall("[\w,]{1,5}", i)

            lcd.lcd_show(
                first_row="FS  used  free",
                second_row="/   {0: <4}  {1: <4}".format(root[3], root[4])
            )
        elif "/dev/sda" in i:
            # 'Filesystem      Size  Used Avail Use% Mounted on'
            # '/dev/sda1       294G   58G  222G  21% /media'
            sda = re.findall("[\w,]{1,5}", i)

            lcd.lcd_show(
                first_row="FS  used  free",
                second_row="sda {0: <4}  {1: <4}".format(sda[3], sda[4])
            )


while run_service.is_set():
    show_weather_log()

    show_docker_ps()

    show_up_time()

    show_df()
