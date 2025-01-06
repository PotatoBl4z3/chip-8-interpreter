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
    key_inputs = [0]*16
    opcode = 0
    index = 0
    pc = 0
    delay_timer = 0
    sound_timer = 0
    
    should_draw = False
    key_wait = False
    
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
    buzz = pyglet.resource.media('buzz.wav', streaming=False)
    
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
        
        binary = []
        
        with open(rom_path, 'rb') as f:
            program = f.read()
            
            for i in program:
                binary.append(i)
        
        i = 0
        while i < len(binary):
            self.memory[i+0x200] = binary[i]
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
            self.flip() 
            self.should_draw = False
            
    def cycle(self):
        self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1] # takes the first byte at pc, pushes it left by 8 bits to make space for the next byte and use the bitwise OR operator to add it to the first byte to get the opcode
        
        #Process the opcode
        self.first_nibble = self.opcode & 0xf000 # extracts the first nibble
        self.x = (self.opcode & 0x0f00) >> 8 # extracts the second nibble 
        self.y = (self.opcode & 0x00f0) >> 4 # extracts the third nibble
        self.n = self.opcode & 0x000f # extracts the fourth nibble
        self.nn = self.opcode & 0x00ff # extracts the last byte
        self.nnn = self.opcode & 0x0fff # extracts the last 12 bits
        
        self.pc += 2
        
        #Opcode decoding if-else statements
        if (self.first_nibble == 0x0000):
            if (self.opcode == 0x00e0):
                log("Clears Screen")
                self.display_buffer = [0] * 64 * 32 # resets the display buffer
                self.should_draw = True
            elif (self.opcode == 0x00ee):
                log("Returns from subroutine")
                self.pc = self.stack.pop()
        
        elif (self.first_nibble == 0x1000):
            log("Jumps to address NNN")
            self.pc = self.nnn
            
        elif (self.first_nibble == 0x2000):
            log("Calls subroutine at NNN")
            self.stack.append(self.pc)
            self.pc = self.nnn
            
        elif (self.first_nibble == 0x3000):
            log("Skips the next instruction if VX equals NN")
            if (self.v[self.x] == self.nn):
                self.pc += 2
        
        elif (self.first_nibble == 0x4000):
            log("Skips the next instruction if VX does not equals NN")
            if (self.v[self.x] != self.nn):
                self.pc += 2
        
        elif (self.first_nibble == 0x5000):
            log("Skips the next instruction if VX equals VY")
            if (self.v[self.x] == self.v[self.y]):
                self.pc += 2
            
        elif (self.first_nibble == 0x6000):
            log("Sets VX to NN")
            self.v[self.x] = self.nn
        
        elif (self.first_nibble == 0x7000):
            log("Adds NN to VX")
            self.v[self.x] += self.nn
            
        elif (self.first_nibble == 0x8000):
            if (self.n == 0x0):
                log("Sets VX to the value of VY")
                self.v[self.x] = self.v[self.y]
            
            elif (self.n == 0x1):
                log("Sets VX to VX or VY")
                self.v[self.x] |= self.v[self.y]
                
            elif (self.n == 0x2):
                log("Sets VX to VX and VY")
                self.v[self.x] &= self.v[self.y]
                
            elif (self.n == 0x3):
                log("Sets VX to VX XOR VY")
                self.v[self.x] ^= self.v[self.y]
                
            elif (self.n == 0x4):
                log("Sets VX = VX + VY")
                if (self.v[self.x] + self.v[self.y] > 0xff): # Checking whether the sum is greater than 1 byte or not
                    self.v[0xf] = 1
                else:
                    self.v[0xf] = 0
                self.v[self.x] += self.v[self.y]
                self.v[self.x] &= 0xff # Only use the last 8 bits or 1 byte
            
            elif (self.n == 0x5):
                log("Sets VX = VX - VY")
                if (self.v[self.x] > self.v[self.y]):
                    self.v[0xf] = 1
                else:
                    self.v[0xf] = 0
                self.v[self.x] -= self.v[self.y]
                #self.v[self.x] &= 0xff
                
            elif (self.n == 0x6):
                log("Sets VX = VX and shifts it by 1 bit to the right")
                self.v[0xf] = self.v[self.x] & 0x01 # Storing the least significant bit in VF
                self.v[self.x] = self.v[self.x] >> 1
                
            elif (self.n == 0x7):
                log("Sets VX = VY - VX")
                if (self.v[self.y] > self.v[self.x]):
                    self.v[0xf] = 1
                else:
                    self.v[0xf] = 0
                self.v[self.x] = self.v[self.y] - self.v[self.x]
            
            elif (self.n == 0xe):
                log("Sets VX = VX and shifts it by 1 bit to the left")
                self.v[0xf] = (self.v[self.x] & 0x80) >> 7 # Storing the most significant bit in VF
                self.v[self.x] = self.v[self.x] << 1
                
            
        elif (self.first_nibble == 0x9000):
            log("Skips the next instruction if VX does not equal VY")
            if (self.v[self.x] != self.v[self.y]):
                self.pc += 2
            
        elif (self.first_nibble == 0xa000):
            self.index = self.nnn
            
        elif (self.first_nibble == 0xb000):
            log("Jumps to Address NNN plus V0") # Might need to change this to address XNN plus VX
            self.pc = self.nnn + self.v[0x0]
            
        elif (self.first_nibble == 0xc000):
            log("Generates a random number between 0 and 255, ANDs it with NN and stores it in VX")
            self.v[self.x] = random.randint(0, 255) & self.nn
            self.v[self.x] &= 0xff
            
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
        
        elif (self.first_nibble == 0xe000):
            if (self.n == 0xe):
                log("Skips the next instruction if the key stored in VX is pressed.")
                key = self.v[self.x] & 0xf
                if (self.key_inputs[key] == 1):
                    self.pc += 2
            elif (self.n == 0x1):
                log("Skips the next instruction if the key stored in VX isn't pressed.")
                key = self.v[self.x] & 0xf
                if (self.key_inputs[key] == 0):
                    self.pc += 2
                    
        elif (self.first_nibble == 0xf000):
            if (self.nn == 0x07):
                log("Sets VX to the value of the delay timer")
                self.v[self.x] = self.delay_timer
            
            elif (self.nn == 0x0A):
                log("After a key is pressed, that key is stored in VX")
                key_pressed = self.get_key()
                if (key_pressed >= 0):
                    self.v[self.x] = key_pressed
                else:
                    self.pc -= 2
            
            elif (self.nn == 0x15):
                log("Sets the value of the delay timer to VX")
                self.delay_timer = self.v[self.x]
                
            elif (self.nn == 0x18):
                log("Sets the value of the sound timer to VX")
                self.sound_timer = self.v[self.x]
                
            elif (self.nn == 0x1e):
                log("Adds VX to I")
                self.index += self.v[self.x]
                if (self.index > 0xfff):
                    self.v[0xf] = 1
                    self.index &= 0xfff
                else:
                    self.v[0xf] = 0
                    
            elif (self.nn == 0x29):
                log("Sets I to point to the character of the hexadecimal in VX")
                self.index = int(5*(self.v[self.x])) & 0xfff
                
            elif (self.nn == 0x33):
                log("Stores BCD representation of Vx in memory locations I, I+1, and I+2")
                self.memory[self.index] = self.v[self.x] / 100
                self.memory[self.index+1] = (self.v[self.x] % 100) / 10
                self.memory[self.index+2] = self.v[self.x] % 10
                
            elif (self.nn == 0x55):
                log("Stores the values of V0 through VX starting at memory location I")
                for i in range(0, self.x+1):
                    self.memory[self.index+i] = self.v[i]
            
            elif (self.nn == 0x65):
                log("Reads the values of V0 through VX starting at memory location I")
                for i in range(0, self.x+1):
                    self.v[i] = self.memory[self.index+i]
        
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
        if self.sound_timer != 0:
            # Play a sound here with pyglet
            self.buzz.play()
            
    
    
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