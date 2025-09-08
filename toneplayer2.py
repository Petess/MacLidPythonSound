import pygame
import numpy as np
import sounddevice as sd
import threading
import time

try:
    from pybooklid import LidSensor
    PYBOOKLID_AVAILABLE = True
except ImportError:
    PYBOOKLID_AVAILABLE = False
    print("pybooklid not installed. Lid sensor functionality disabled.")
    print("Install with: pip install pybooklid")

class ToneGenerator:
    def __init__(self):
        # Initialize pygame for keyboard input
        pygame.init()
        pygame.display.set_mode((500, 350))
        pygame.display.set_caption("Tone Generator - W=Up, S=Down, L=Lid Sensor, ESC=Exit")

        # Audio parameters
        self.sample_rate = 44100
        self.base_frequency = 440.0  # A4 note
        self.current_frequency = self.base_frequency
        self.frequency_step = 50  # Hz change per key press
        self.min_frequency = 100
        self.max_frequency = 2000

        # Audio generation
        self.is_playing = False
        self.audio_thread = None
        self.should_stop = False

        # Lid sensor parameters
        self.lid_sensor_enabled = False
        self.lid_sensor_thread = None
        self.current_angle = 0.0
        self.lid_sensor_active = False

    def generate_tone(self, frequency, duration=0.1):
        """Generate a sine wave tone at the given frequency"""
        frames = int(duration * self.sample_rate)
        t = np.linspace(0, duration, frames, False)
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)  # 0.3 amplitude to avoid loud sound
        return wave.astype(np.float32)

    def play_continuous_tone(self):
        """Play a continuous tone that can change frequency"""
        def audio_callback(outdata, frames, time, status):
            if status:
                print(status)

            # Generate tone data for current frequency
            t = np.arange(frames) / self.sample_rate
            wave = 0.3 * np.sin(2 * np.pi * self.current_frequency * t)
            outdata[:] = wave.reshape(-1, 1)

        # Start audio stream
        with sd.OutputStream(callback=audio_callback, samplerate=self.sample_rate, channels=1):
            while not self.should_stop:
                time.sleep(0.01)

    def angle_to_frequency(self, angle):
        """Convert lid angle to frequency"""
        # Map angle (0-180 degrees) to frequency range
        # Clamp angle to reasonable range
        angle = max(0, min(180, angle))

        # Linear mapping: 0 degrees = min_frequency, 180 degrees = max_frequency
        frequency = self.min_frequency + (angle / 180.0) * (self.max_frequency - self.min_frequency)
        return frequency

    def monitor_lid_sensor(self):
        """Monitor the lid sensor and update frequency"""
        try:
            print("Starting lid sensor...")
            with LidSensor() as sensor:
                print("Lid sensor started. Close lid to angle < 10° to stop.")
                self.lid_sensor_active = True

                for angle in sensor.monitor(interval=0.1):
                    if not self.lid_sensor_enabled or self.should_stop:
                        break

                    self.current_angle = angle
                    new_frequency = self.angle_to_frequency(angle)
                    self.current_frequency = new_frequency

                    print(f"Angle: {angle:.1f}° → Frequency: {self.current_frequency:.1f} Hz")

                    if angle < 10:  # Nearly closed
                        print("Lid nearly closed - stopping sensor")
                        break

        except Exception as e:
            print(f"Lid sensor error: {e}")
        finally:
            self.lid_sensor_enabled = False
            self.lid_sensor_active = False
            print("Lid sensor monitoring stopped")

    def start_lid_sensor(self):
        """Start monitoring the lid sensor"""
        if not PYBOOKLID_AVAILABLE:
            print("pybooklid not available")
            return

        if not self.lid_sensor_enabled:
            self.lid_sensor_enabled = True
            self.lid_sensor_thread = threading.Thread(target=self.monitor_lid_sensor)
            self.lid_sensor_thread.daemon = True
            self.lid_sensor_thread.start()

    def stop_lid_sensor(self):
        """Stop monitoring the lid sensor"""
        self.lid_sensor_enabled = False
        if self.lid_sensor_thread and self.lid_sensor_thread.is_alive():
            self.lid_sensor_thread.join(timeout=2)

    def change_frequency(self, direction):
        """Change the current frequency up or down (manual control)"""
        if self.lid_sensor_enabled:
            print("Manual frequency control disabled while lid sensor is active")
            return

        if direction == "up":
            self.current_frequency = min(self.current_frequency + self.frequency_step, self.max_frequency)
        elif direction == "down":
            self.current_frequency = max(self.current_frequency - self.frequency_step, self.min_frequency)

        print(f"Frequency: {self.current_frequency:.1f} Hz")

    def start_audio(self):
        """Start the continuous audio thread"""
        if not self.is_playing:
            self.is_playing = True
            self.should_stop = False
            self.audio_thread = threading.Thread(target=self.play_continuous_tone)
            self.audio_thread.start()

    def stop_audio(self):
        """Stop the continuous audio thread"""
        if self.is_playing:
            self.should_stop = True
            if self.audio_thread:
                self.audio_thread.join()
            self.is_playing = False

    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True

        print("Tone Generator Started!")
        print("Controls:")
        print("W - Increase frequency (manual mode)")
        print("S - Decrease frequency (manual mode)")
        print("SPACE - Start/Stop continuous tone")
        if PYBOOKLID_AVAILABLE:
            print("L - Start/Stop lid sensor monitoring")
        print("ESC - Exit")
        print(f"Current frequency: {self.current_frequency:.1f} Hz")

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_w:
                        self.change_frequency("up")
                        # Play a short beep to demonstrate the new frequency
                        if not self.is_playing:
                            tone = self.generate_tone(self.current_frequency, 0.2)
                            sd.play(tone, self.sample_rate)

                    elif event.key == pygame.K_s:
                        self.change_frequency("down")
                        # Play a short beep to demonstrate the new frequency
                        if not self.is_playing:
                            tone = self.generate_tone(self.current_frequency, 0.2)
                            sd.play(tone, self.sample_rate)

                    elif event.key == pygame.K_SPACE:
                        if self.is_playing:
                            self.stop_audio()
                            print("Continuous tone stopped")
                        else:
                            self.start_audio()
                            print("Continuous tone started")

                    elif event.key == pygame.K_l and PYBOOKLID_AVAILABLE:
                        if not self.lid_sensor_enabled:
                            self.start_lid_sensor()
                            print("Starting lid sensor...")
                        else:
                            self.stop_lid_sensor()
                            print("Stopping lid sensor...")

            # Fill screen with color based on frequency (visual feedback)
            frequency_ratio = (self.current_frequency - self.min_frequency) / (self.max_frequency - self.min_frequency)
            color_intensity = int(255 * frequency_ratio)
            screen_color = (color_intensity, 100, 255 - color_intensity)

            screen = pygame.display.get_surface()
            screen.fill(screen_color)

            # Display frequency and angle on screen
            font = pygame.font.Font(None, 36)
            text = font.render(f"Frequency: {self.current_frequency:.1f} Hz", True, (255, 255, 255))
            text_rect = text.get_rect(center=(250, 80))
            screen.blit(text, text_rect)

            # Display angle if lid sensor is active
            if self.lid_sensor_enabled or self.lid_sensor_active:
                angle_text = font.render(f"Lid Angle: {self.current_angle:.1f}°", True, (255, 255, 255))
                angle_rect = angle_text.get_rect(center=(250, 120))
                screen.blit(angle_text, angle_rect)

            # Display controls
            font_small = pygame.font.Font(None, 20)
            controls = [
                "W - Frequency Up (manual)",
                "S - Frequency Down (manual)",
                "SPACE - Start/Stop Continuous Tone"
            ]

            if PYBOOKLID_AVAILABLE:
                controls.append("L - Start/Stop Lid Sensor")
                if self.lid_sensor_enabled:
                    controls.append("Lid Sensor: ACTIVE")
                else:
                    controls.append("Lid Sensor: INACTIVE")

            controls.extend([
                "ESC - Exit",
                "",
                "Mode: " + ("Lid Sensor" if self.lid_sensor_enabled else "Manual")
            ])

            for i, control in enumerate(controls):
                if control:  # Skip empty strings
                    control_text = font_small.render(control, True, (255, 255, 255))
                    screen.blit(control_text, (10, 180 + i * 22))

            pygame.display.flip()
            clock.tick(60)

        # Cleanup
        self.stop_audio()
        self.stop_lid_sensor()
        pygame.quit()
        print("Tone Generator closed.")

if __name__ == "__main__":
    try:
        generator = ToneGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have the required packages installed:")
        print("pip install pygame numpy sounddevice pybooklid")
