from time import sleep

from i2c_driver import I2C_driver

__author__ = "Evgeny Goncharov"

# commands
LCD_CLEAR_DISPLAY = 0x01
LCD_RETURN_HOME = 0x02
LCD_ENTRY_MODE_SET = 0x04
LCD_DISPLAY_CONTROL = 0x08
LCD_CURSOR_SHIFT = 0x10
LCD_FUNCTION_SET = 0x20
LCD_SET_CGRAM_ADDR = 0x40
LCD_SET_DDRAM_ADDR = 0x80

# flags for display entry mode
LCD_ENTRY_RIGHT = 0x00
LCD_ENTRY_LEFT = 0x02
LCD_ENTRY_SHIFT_INCREMENT = 0x01
LCD_ENTRY_SHIFT_DECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAY_ON = 0x04
LCD_DISPLAY_OFF = 0x00
LCD_CURSOR_ON = 0x02
LCD_CURSOR_OFF = 0x00
LCD_BLINK_ON = 0x01
LCD_BLINK_OFF = 0x00

# flags for display/cursor shift
LCD_DISPLAY_MOVE = 0x08
LCD_CURSOR_MOVE = 0x00
LCD_MOVE_RIGHT = 0x04
LCD_MOVE_LEFT = 0x00

# flags for function set
LCD_8_BIT_MODE = 0x10
LCD_4_BIT_MODE = 0x00
LCD_2_LINE = 0x08
LCD_1_LINE = 0x00
LCD_5x10_DOTS = 0x04
LCD_5x8_DOTS = 0x00

# flags for backlight control
LCD_BACK_LIGHT = 0x08
LCD_NO_BACK_LIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class LCD:
    # initializes objects and lcd
    def __init__(self, address, port):
        self.lcd_device = I2C_driver(address=address, port=port)

        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        self.lcd_write(
            LCD_FUNCTION_SET | LCD_2_LINE |
            LCD_5x8_DOTS | LCD_4_BIT_MODE
        )
        self.lcd_write(
            LCD_DISPLAY_CONTROL | LCD_DISPLAY_ON
        )
        self.lcd_write(LCD_CLEAR_DISPLAY)
        self.lcd_write(
            LCD_ENTRY_MODE_SET | LCD_ENTRY_LEFT
        )

        sleep(0.2)

    # clocks EN to latch command
    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(
            data | En | LCD_BACK_LIGHT
        )
        sleep(.0005)
        self.lcd_device.write_cmd(
            ((data & ~En) | LCD_BACK_LIGHT)
        )
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACK_LIGHT)
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def lcd_write_char(self, char_value, mode=1):
        self.lcd_write_four_bits(mode | (char_value & 0xF0))
        self.lcd_write_four_bits(mode | ((char_value << 4) & 0xF0))

    # put string function with optional char positioning
    def lcd_display_string(self, string, line=1, pos=0):
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        self.lcd_write(0x80 + pos_new)

        for char in string:
            self.lcd_write(ord(char), Rs)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(LCD_CLEAR_DISPLAY)
        self.lcd_write(LCD_RETURN_HOME)

    # define backlight on/off (lcd.back_light(1); off= lcd.back_light(0)
    def back_light(self, state):  # for state, 1 = on, 0 = off
        if state == 1:
            self.lcd_device.write_cmd(LCD_BACK_LIGHT)
        elif state == 0:
            self.lcd_device.write_cmd(LCD_NO_BACK_LIGHT)

    # add custom characters (0 - 7)
    def lcd_load_custom_chars(self, font_data):
        self.lcd_write(0x40)
        for char in font_data:
            for line in char:
                self.lcd_write_char(line)

    def lcd_show(self, first_row=None, second_row=None):
        self.lcd_clear()

        if first_row:
            self.lcd_display_string(first_row, 1)

        if second_row:
            self.lcd_display_string(second_row, 2)
