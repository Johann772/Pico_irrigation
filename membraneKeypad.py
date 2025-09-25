import rp2
from rp2 import PIO
from machine import Pin

class Keypad():
    def __init__(self, sm_id=0, in_base=12, set_base=8, callback=None):
        self.key_names = "*7410852#963DCBA"
        self.callback = callback
        self.last_key = None

        # Configure input pins with pull-downs
        for i in range(in_base, in_base + 4):
            Pin(i, Pin.IN, Pin.PULL_DOWN)

        self.sm = rp2.StateMachine(
            sm_id,
            Keypad.pio_program,
            freq=2000,
            in_base=Pin(in_base, Pin.IN, Pin.PULL_DOWN),
            set_base=Pin(set_base)
        )
        self.sm.irq(self._on_input)
        self.sm.active(1)

    def _on_input(self, sm):
        keys = sm.get()
        while sm.rx_fifo():
            keys = sm.get()
        for i in range(len(self.key_names)):
            if keys & (1 << i):
                key = self.key_names[i]
                self.last_key = key
                if self.callback:
                    self.callback(key)
                break

    def get_last_key(self):
        return self.last_key

    @staticmethod
    @rp2.asm_pio(set_init=[PIO.IN_HIGH]*4)
    def pio_program():
        wrap_target()
        set(y, 0)                             # 0
        label("1")
        mov(isr, null)                        # 1
        set(pindirs, 1)                       # 2
        in_(pins, 4)                          # 3
        set(pindirs, 2)                       # 4
        in_(pins, 4)                          # 5
        set(pindirs, 4)                       # 6
        in_(pins, 4)                          # 7
        set(pindirs, 8)                       # 8
        in_(pins, 4)                          # 9
        mov(x, isr)                           # 10
        jmp(x_not_y, "13")                    # 11
        jmp("1")                              # 12
        label("13")
        push(block)                           # 13
        irq(0)
        mov(y, x)                             # 14
        jmp("1")                              # 15
        wrap()

    