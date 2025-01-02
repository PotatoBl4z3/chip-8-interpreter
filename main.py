import itertools
import os
import pyglet
import random
import sys
import time

from pyglet.sprite import Sprite

KEY_MAP = {pyglet.window.key._1: 0x1,
           pyglet.window.key._2: 0x2,
           pyglet.window.key._3: 0x3,
           pyglet.window.key._4: 0xc,
           pyglet.window.key.Q: 0x4,
           pyglet.window.key.W: 0x5,
           pyglet.window.key.E: 0x6,
           pyglet.window.key.R: 0xd,
           pyglet.window.key.A: 0x7,
           pyglet.window.key.S: 0x8,
           pyglet.window.key.D: 0x9,
           pyglet.window.key.F: 0xe,
           pyglet.window.key.Z: 0xa,
           pyglet.window.key.X: 0,
           pyglet.window.key.C: 0xb,
           pyglet.window.key.V: 0xf
          }

LOGGING = False

def log(msg):
  if LOGGING:
    print(msg)

class cpu (pyglet.window.Window):
    memory = [0]*4096 # max 4096 bits
    v = [0]*16 # max 16 bits
    display_buffer = [0]*32*64 # 64*32 display size
    stack = []
    opcode = 0
    index = 0
    pc = 0
    delay_timer = 0
    sound_timer = 0
    
    should_draw = False
    
    fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
           0x20, 0x60, 0x20, 0x20, 0x70, # 1
           0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
           0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
           0x90, 0x90, 0xF0, 0x10, 0x10, # 4
           0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
           0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
           0xF0, 0x10, 0x20, 0x40, 0x40, # 7
           0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
           0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
           0xF0, 0x90, 0xF0, 0x90, 0x90, # A
           0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
           0xF0, 0x80, 0x80, 0x80, 0xF0, # C
           0xE0, 0x90, 0x90, 0x90, 0xE0, # D
           0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
           0xF0, 0x80, 0xF0, 0x80, 0x80  # F
           ]
    
    pixel = pyglet.resource.image('pixel.png')
    
    first_nibble = 0
    x = 0
    y = 0
    n = 0
    nn = 0
    nnn = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def initialize(self):
        self.clear()
        self.memory = [0]*4096 # max 4096 bytes of memory
        self.v = [0]*16 # max 16 bytes
        self.display_buffer = [0]*64*32 # 64*32 display size
        self.stack = []
        self.key_inputs = [0]*16  
        self.opcode = 0
        self.index = 0
        
        self.delay_timer = 0
        self.sound_timer = 0
        self.should_draw = False
    
        self.pc = 0x200 # 0x000 to 0x200 is reserved so we start from 0x200
    
        i = 0
        while i < 80:
            # load 80-char font set
            self.memory[i] = self.fonts[i]
            i += 1
    
    def get_key(self):
        i = 0
        while i < 16:
            if self.key_inputs[i] == 1:
                return i
            i += 1
        return -1
    
    def on_key_press(self, symbol, modifiers):
        log("Key pressed: %r" % symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 1
        if self.key_wait:
            self.key_wait = False
        else:
            super(cpu, self).on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        log("Key released: %r" % symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 0
    
    def load_rom(self, rom_path):
        log("Loading %s..." % rom_path)
        binary = open(rom_path, "rb").read()
        i = 0
        while i < len(binary):
            self.memory[i+0x200] = ord(binary[i])
            i += 1
            
    def draw(self):
        if self.should_draw:
            # draw
            self.clear()
            line_counter = 0
            i = 0
            while i < 2048:
                if self.display_buffer[i] == 1:
                    #draw a pixel
                    self.pixel.blit((i%64)*10, 310-((i/64)*10))
                i += 1
            self.batch.draw()
            self.flip() 
            self.should_draw = False
            
    def cycle(self):
        self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1] # takes the first byte at pc, pushes it left by 8 bits to make space for the next byte and use the bitwise OR operator to add it to the first byte to get the opcode
        
        #TODO: Process the opcode
        self.first_nibble = self.opcode & 0xf000 # extracts the first nibble
        self.x = (self.opcode & 0x0f00) >> 8 # extracts the second nibble 
        self.y = (self.opcode & 0x00f0) >> 4 # extracts the third nibble
        self.n = self.opcode & 0x000f # extracts the last nibble
        self.nn = self.opcode & 0x00ff # extracts the last byte
        self.nnn = self.opcode & 0x0fff # extracts the last 12 bits
        
        self.pc += 2
        
        #Opcode decoding if-else statements
        if (self.first_nibble == 0x0000):
            if (self.opcode == 0x00e0):
                log("Clear Screen")
                self.display_buffer = [0] * 64 * 32 # resets the display buffer
                self.should_draw = True
            elif (self.opcode == 0x00ee):
                log("Return")
                self.pc = self.stack.pop()
        
        elif (self.first_nibble == 0x1000):
            self.pc = self.nnn
            
        elif (self.first_nibble == 0x6000):
            self.v[self.x] = self.nn
        
        elif (self.first_nibble == 0x7000):
            self.v[self.x] += self.nn
            
        elif (self.first_nibble == 0xa000):
            self.index = self.nnn
            
        elif (self.first_nibble == 0xd000):
            log("Draw a sprite")
            self.v[0xf] = 0 # setting VF to 0
            x = self.v[self.x] & 0xff
            y = self.v[self.y] & 0xff
            row = 0
            while row < self.n: # drawing a sprite of width 8 pixels and height n pixels
                curr_row = self.memory[row + self.index]
                pixel_offset = 0
                while pixel_offset < 8:
                    loc = x + pixel_offset + ((y + row) * 64) # find the display buffer location
                    pixel_offset += 1
                    if (y + row) >= 32 or (x + pixel_offset - 1) >= 64:
                        # ignore pixels outside the screen
                        continue
                    mask = 1 << 8-pixel_offset
                    curr_pixel = (curr_row & mask) >> (8-pixel_offset)
                    self.display_buffer[loc] ^= curr_pixel
                    if self.display_buffer[loc] == 0:
                        self.v[0xf] = 1
                    else:
                        self.v[0xf] = 0
                row += 1
            self.should_draw = True
        
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
        if self.sound_timer == 0:
            # Play a sound here with pyglet
            return #TODO: Placeholder
    
    
    def main(self):
        
        self.initialize()
        self.load_rom(sys.argv[1])
        while not self.has_exit:
            self.dispatch_events()
            self.cycle()
            self.draw()

if len(sys.argv) == 3:
  if sys.argv[2] == "log":
    LOGGING = True
      
chip8emu = cpu(640, 320)
chip8emu.main()
log("... done.")