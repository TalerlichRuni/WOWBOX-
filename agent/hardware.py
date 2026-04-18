import time
import threading
from rpi_ws281x import PixelStrip, Color

# LED strip configuration:
LED_COUNT = 12
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

class LEDController:
    def __init__(self):
        self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.stop_event = threading.Event()
        self.thread = None
        self.off()

    def off(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def set_color(self, red, green, blue):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(red, green, blue))
        self.strip.show()

    def _heartbeat_worker(self):
        """The animation loop running in a background thread."""
        R, G, B = 255, 0, 100
        while not self.stop_event.is_set():
            # Fade in
            for i in range(0, 101, 2):
                if self.stop_event.is_set(): break
                brightness = i / 100.0
                self.set_color(int(R * brightness), int(G * brightness), int(B * brightness))
                time.sleep(0.01)
            
            if not self.stop_event.is_set(): time.sleep(0.1)
            
            # Fade out
            for i in range(100, -1, -2):
                if self.stop_event.is_set(): break
                brightness = i / 100.0
                self.set_color(int(R * brightness), int(G * brightness), int(B * brightness))
                time.sleep(0.01)
            
            if not self.stop_event.is_set(): time.sleep(0.5)
        self.off()

    def start_heartbeat(self):
        """Start the heartbeat in a background thread."""
        if self.thread and self.thread.is_alive():
            return 
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._heartbeat_worker)
        self.thread.daemon = True
        self.thread.start()

    def stop_heartbeat(self):
        """Signal the heartbeat to stop."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
        self.off()

# Singleton instance
leds = None
def get_leds():
    global leds
    if leds is None:
        leds = LEDController()
    return leds
