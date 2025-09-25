from machine import mem32, disable_irq, enable_irq

GPIO0_CTRL = 0x40014000+0x004 
SIO_BASE       = 0xd0000000
GPIO_OE_SET    = SIO_BASE + 0x024  # Atomic SET
GPIO_OE = SIO_BASE + 0x020
GPIO_OUT       = SIO_BASE + 0x10  # Direct OUT register
GPIO_OUT_SET   = SIO_BASE + 0x14  # Atomic set bits
GPIO_OUT_CLR   = SIO_BASE + 0x18  # Atomic clear bits
PIN_MASK = 0xFF

def setOutputs(pins: tuple):
    mask = 0
    for p in pins:
        if 0 <= p <= 7:  # restrict to pins 0–7
            mem32[GPIO0_CTRL + 8 * p] = 5  # function = SIO
            mask |= 1 << p

    if mask:
        mem32[GPIO_OE_SET] = mask  # atomic set bits

def setSioOutRegister(val):
    # Ensure 0-7 bits only
    val &= PIN_MASK

    # Disable interrupts for atomicity (works across cores)
    #state = disable_irq()

    # Clear bits 0-7
    mem32[GPIO_OUT_CLR] = PIN_MASK
    # Set bits from val
    mem32[GPIO_OUT_SET] = val

    # Restore interrupts
    #enable_irq(state)

