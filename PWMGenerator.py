import logging
import math
import time

from threading import RLock

import pigpio

# Abstract base class for Servos and bi-directional motors
#
class PWMGenerator:
    
    def __init__(self, name, gpio_pin, min_pos, max_pos):
        self.name = name
        
        # GPIO pin to which the servo is connected
        self.pin = gpio_pin
        
        # Pulse widths for the extreme positions of the servo. 
        # These values are specified in uS 
        self.min = min_pos
        self.max = max_pos
        
        # Init the servo pin and move the servo to the center (neutral) position
        self._pigpio_init_pwm()
        
        # Syncronization of methods that we do not want executing concurrently
        self.lock = RLock()
    
    def _pigpio_init_pwm(self):
#        pigpio.set_PWM_frequency(self.pin, 50) # 50Hz pulses
#        pigpio.set_PWM_range(self.pin, 20000) # 1,000,000 / 50 = 20,000us for 100% duty cycle
#        self.logger.info("PWM cycle frequency: %dHz" % pigpio.get_PWM_frequency(self.pin))
        pass
    
    # Change the duty cycle slowly and smoothly to the specified position
    # The speed is controlled by STEP. Smoothness by SLEEP.
    def smooth_set_duty_cycle(self, pulse_width_us):
        self.lock.acquire()
        
        # We always change pulse width in multiple of STEP, and we must always keep the value
        # in the specified range. This code will make sure that all the conditions are true,
        # just in case someone is fucking around
        #
        
        # Make it a multiple of STEP
        pulse_width_us = (pulse_width_us / self.STEP) * self.STEP
        
        # Make sure that we are within bounds
        if ( pulse_width_us < self.min ): pulse_width_us = self.min
        if ( pulse_width_us > self.max ): pulse_width_us = self.max
        
        # If we are just getting started, there might be not current pulse width yet
        if ( self.current_pulse_width < self.min ): self.current_pulse_width = self.min 
        
        
        if self.current_pulse_width < pulse_width_us:
            # We need to increase the duty cycle
            while self.increase_duty_cycle() < pulse_width_us :
                time.sleep(self.SLEEP)
        if self.current_pulse_width > pulse_width_us:
            # We need to decrease the duty cycle
            while self.decrease_duty_cycle() > pulse_width_us :
                time.sleep(self.SLEEP)
        else:
            self.set_duty_cycle(pulse_width_us)
        
        self.lock.release()

    # Decrease by STEP
    def decrease_duty_cycle(self):
        self.lock.acquire()
        try:
            desired_pulse_width_us = self.current_pulse_width - self.STEP
            if ( desired_pulse_width_us >= self.min ):
                self.set_duty_cycle(desired_pulse_width_us)
                self.current_pulse_width = desired_pulse_width_us
                return self.current_pulse_width
            else:
                return False
            
        finally:
            self.lock.release()
        
    # Increase by STEP
    def increase_duty_cycle(self):
        self.lock.acquire()
        try:
            desired_pulse_width_us = self.current_pulse_width + self.STEP
            if ( desired_pulse_width_us <= self.max ):
                self.set_duty_cycle(self.current_pulse_width + self.STEP)
                self.current_pulse_width = desired_pulse_width_us
                return self.current_pulse_width
            else:
                return False
        finally:
            self.lock.release()
        
    
    # WARNING: This method can only be called from the same thread where the network socket event loop is running! 
    def print_servo_position(self, android_socket):
        self.android_socket.push("%s:%s\n" % self.name, self.current_pulse_width)
        
    # Abstract methods
    #        
    def set_duty_cycle(self, pulse_width_us):
        raise NotImplementedError("Please Implement this method")
    
    def stop_device(self):
        raise NotImplementedError("Please Implement this method")
