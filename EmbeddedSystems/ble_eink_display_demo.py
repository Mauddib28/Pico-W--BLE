###
# The purpose of this script is to provide a Bluetooth Low Energy target that can:
#   - Display information via Wave Share 2in13 V4 E-Ink Display
#   - Provide R/W I/O as well as notifications for further device training
#   - Expand learning for more advanced BLE device and tool development
###

import bluetooth
from machine import Pin, SPI
import struct
import time
from micropython import const
from ble_advertising import advertising_payload
import framebuf
# Import for display to Waveshare E-Ink Display
from Pico_ePaper_2_13_V4 import EPD_2in13_V4_Portrait, EPD_2in13_V4_Landscape

# Debugging flag
dbg = 0

# IRQ Event Constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)

# Flag Constants
_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# Service UUID for E-Ink Display Demo
_EINK_UUID = bluetooth.UUID("E1234000-A5A5-F5F5-C5C5-111122223333")

# Read Characteristics
_READ_BUFFER = (
    bluetooth.UUID("E1234001-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_READ | _FLAG_NOTIFY,
)

_READ_STATUS = (
    bluetooth.UUID("E1234002-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_READ,
)

# Write Characteristics
_WRITE_DISPLAY = (
    bluetooth.UUID("E1234003-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_WRITE,
)

_WRITE_COMMAND = (
    bluetooth.UUID("E1234004-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_WRITE,
)

# Add these constants near your other UUID definitions
_NOTIFY_STATUS = (
    bluetooth.UUID("E1234005-A5A5-F5F5-C5C5-111122223333"),
    _FLAG_READ | _FLAG_NOTIFY,
)

# Combine all characteristics into one service
_EINK_SERVICE = (
    _EINK_UUID,
    (_READ_BUFFER, _READ_STATUS, _WRITE_DISPLAY, _WRITE_COMMAND, _NOTIFY_STATUS),
)

## BLE Class Definition
class BLEEinkDisplay:
    def __init__(self, ble, eink_display, name="eink-display"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._eink = eink_display  # E-ink display object
        
        # Register services
        ((self._handle_read_buffer,
          self._handle_read_status,
          self._handle_write_display,
          self._handle_write_command,
          self._handle_notify_status),) = self._ble.gatts_register_services((_EINK_SERVICE,))
        
        # Initialize characteristics
        self._ble.gatts_write(self._handle_read_buffer, b'Empty Buffer')
        self._ble.gatts_write(self._handle_read_status, b'Ready')
        self._ble.gatts_write(self._handle_notify_status, b'System Ready')
        
        self._connections = set()
        self._read_buffer = ""
        self._display_text = ""

        self._display_template = False  # Tracking if a template is being used for writes to E-Ink Display
        
        # Split advertising to stay within size limits
        adv_data = advertising_payload(services=[_EINK_UUID])
        resp_data = advertising_payload(name=name)
        self._ble.gap_advertise(500000, adv_data=adv_data, resp_data=resp_data)
        
        if dbg:
            print("[+] BLE E-Ink Display service initialized")

    def notify_all(self, data):
        """Send notification to all connected devices"""
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_notify_status, data)

    def _update_status_and_notify(self, status, operation=None):
        """Update status and notify connected devices"""
        if operation:
            notify_msg = f"{operation} - {status}"
        else:
            notify_msg = status
            
        if dbg:
            print(f"[*] Status Update: {notify_msg}")
            
        # Update status characteristic
        self._ble.gatts_write(self._handle_read_status, status.encode())
        # Send notification
        self.notify_all(notify_msg.encode())

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            if dbg:
                print(f"[+] Connected: {conn_handle}")
            self._connections.add(conn_handle)
            self._update_status_and_notify("Connected", "Connection")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if dbg:
                print(f"[-] Disconnected: {conn_handle}")
            self._connections.remove(conn_handle)
            self._update_status_and_notify("Disconnected", "Connection")
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            value = self._ble.gatts_read(attr_handle)

            # Nota Bene: Making the call to run the E-Ink displays SLOWS DOWN EVERYTHING!!!
            #   - One can artificially slow down the Bluetooth Low Energy State Machine
            if attr_handle == self._handle_write_display:
                if dbg:
                    print(f"[*] Display write: {value}")

                # Use to change write display mode
                safe_write_flag = False

                # Check if writing TEMPLATE WRITE or SANITY ASCII WRITE to the E-Ink Display
                if safe_write_flag:
                    # Perform the ASCii Safe Test Write to the Display String
                    self._display_text = self.ascii_safe_encoding(value)


                    if dbg:
                        print(f"[*] AS-Mode - Displaying: {self._display_text}")

                    #self._display_text = value.decode()
                    self._eink.display_text(self._display_text)
                    self._update_status_and_notify("Display updated", "Write")
                else:
                    # Perform the Template Based Write; NOTE: Will require COMPLETE SCREEN CLEAR upon write completion????
                    #print("OTHER TESTING")
                    if not self._display_template:
                        print("[*] Setting the Display Template")
                        # Create the Base Template
                        self._eink.fill(0xFF)
                        start_line = 10
                        start_line = fit_text(self._eink, " -[ BLE Write ]- ", start_line, 30)      # Write on 10
                        start_line = fit_text(self._eink, " Conn Handle: ", start_line, 30)         # Write on 30
                        start_line = fit_text(self._eink, " Attr Handle: ", start_line, 30)         # Write on 50
                        start_line += 30
                        start_line = fit_text(self._eink, " Value: ", start_line, 30)                               # Write on 100 (50 + 20 + 30)
                        # Set the Display Base
                        self._eink.Display_Base(self._eink.buffer)
                        self._eink.delay_ms(500)        # Quick added wait for good measure
                        # Set the Template Flag
                        self._display_template = True
                    else:
                        print("[*] Template Already Set")
                    
                    # Continue with Writing an Update to the Template
                    def mask_and_write(text_string, text_column, text_row, row_width, col_width, write_strength=0xFF):
                        # Variables
                        pixel_char_width = 10

                        # Create the Fill Space Rectangle
                        self._eink.fill_rect(text_row-1, text_column-1, row_width*pixel_char_width, col_width*pixel_char_width, write_strength)

                        # Carve out the Desired Text
                        self._eink.text(text_string, text_row, text_column, 0xFF-write_strength)    # Note: Should produce the opposite of the write strneght?? Overflow testing space
                        #self._eink.text(text_string, text_row, text_column, 0x00)

                    value_fields = None
                    # Produce any text chunking
                    if len(value) > 30:
                        value_fields = list(chunkstring(value, 30))
                    
                    # Safe Variable
                    #safe_conn_handle = self.ascii_safe_encoding(str(conn_handle))
                    #safe_attr_handle = self.ascii_safe_encoding(str(attr_handle))

                    # Make a mask for each piece of information
                    #mask_and_write(safe_conn_handle, 30, 60, len(safe_conn_handle), 1)     # Write the Connection Handle Value
                    #mask_and_write(safe_attr_handle, 50, 60, len(safe_attr_handle), 1)     # Write the Attribute Handle Value
                    mask_and_write(str(conn_handle), 30, 120, len(str(conn_handle)), 1)     # Write the Connection Handle Value
                    mask_and_write(str(attr_handle), 50, 120, len(str(attr_handle)), 1)     # Write the Attribute Handle Value

                    # Special Checks and Mask for the Written Data
                    if value_fields:
                        # Perform Special Write to Map
                        print("DO SOMETHING!")
                    else:
                        # Safe Print
                        safe_value = self.ascii_safe_encoding(value)
                        # Perform a Normal Masking to the Screen
                        #mask_and_write(value, 100, 100, len(value), 1)       # Write the Value Received
                        mask_and_write(safe_value, 100, 60, len(safe_value), 1)       # Write the Value Received
                        # NOTE: Current issue is that the previous mask for the data is not cleared before the new data is written

                    # Display the Partial to the Screen
                    self._eink.displayPartial(self._eink.buffer)
                
            elif attr_handle == self._handle_write_command:
                if dbg:
                    print(f"[*] Command write: {value}")
                cmd = value.decode()
                self._handle_command(cmd)
                self._update_status_and_notify(f"Command executed: {cmd}", "Command")

        elif event == _IRQ_GATTS_READ_REQUEST:
            conn_handle, attr_handle = data
            if dbg:
                print(f"[*] Read request - handle: {attr_handle}")
            
            if attr_handle == self._handle_read_buffer:
                # Update the Read Buffer
                self._update_read_buffer()
                # Send Notifications
                

    def _update_status(self, status):
        if dbg:
            print(f"[*] Status: {status}")
        self._ble.gatts_write(self._handle_read_status, status.encode())

    def _update_read_buffer(self):
        """Update read buffer with current display state"""
        buffer_text = f"Display: {self._display_text}"
        self._ble.gatts_write(self._handle_read_buffer, buffer_text.encode())
        if dbg:
            print(f"[*] Buffer updated: {buffer_text}")
        self._update_status_and_notify("Buffer read", "Read")

    def _handle_command(self, cmd):
        """Handle display commands"""
        if cmd == "clear":
            self._eink.init()
            self._eink.Clear()
            self._eink.delay_ms(500)
            self._eink.sleep()
            self._display_text = ""
            #sleep_display(self._eink)
            self._update_status_and_notify("Display cleared", "Command")
        elif cmd == "refresh":
            self._eink.display_frame()
            self._update_status_and_notify("Display refreshed", "Command")
        elif cmd == "shake":
            self._eink.init()
            self._eink.Clear()
            self._update_status_and_notify("Display Memory Shook", "Command")
        else:
            self._update_status_and_notify(f"Unknown command: {cmd}", "Command")

    def _advertise(self, interval_us=500000):
        adv_data = advertising_payload(services=[_EINK_UUID])
        self._ble.gap_advertise(interval_us, adv_data=adv_data)

    # Internal Function for Producing an ASCii Safe String for Debugging Crashfree
    #   - Example:  Writing 0x79 followed by 0x80 can cause IRQ failure
    def ascii_safe_encoding(self, value):
        # Check if the value contains printable ASCii
        is_ascii = all(32 <= b <= 126 for b in value)

        if is_ascii:
            return value.decode('ascii') + " [ASCII]"
        else:
            # Convert to hex representation
            hex_str = ' '.join(f'0x{b:02X}' for b in value)
            return hex_str + " [HEX]"

## Function Definitions

# Function for Chunking a Provided String
def chunkstring(string, length):
    return (string[0+i:length+i] for i in range (0, len(string), length))

# Function for Fitting Text within the E-Ink Display
def fit_text(epd, text_string, current_line, width_limit):
    # Chunk the strings and fit into the EPD Buffer
    for chunk in chunkstring(text_string, width_limit):
        #print("Chunk:\t".format(chunk))
        epd.text(chunk, 0, current_line, 0x00)
        current_line += 20

    # Return the line now on
    return current_line        # Note: Required to Move the Current Line Along

# Function for Creating a Display Template
def set_display_template(epd, header_string, implementation_string, bottom_string, starting_line, bottom_line):
    # Variables
    max_char_width = 30

    # Fit the Header Text within the Template
    starting_line = fit_text(epd, header_string, starting_line, max_char_width)

    # Fit the Implementation Text within the Template
    starting_line = fit_text(epd, implementation_string, starting_line, max_char_width)

    # Set the Bottom of the Display Template
    epd.text(bottom_string, 0, bottom_line, 0x00)

# Function for Creating a Update Field in the Display
def set_partial_display(epd, text_row, text_column, optional_array=10):
    # Variables
    pixel_per_char = 10

    # Initialize the Display
    epd.init()

    # Determine What Type of Display Update will be done
    if optional_array == 10:
        # Display a Count in the Partial Location
        for i in range(0, optional_array):
            epd.fill_rect(text_row-1, text_column-1, 10, 10, 0xff)      # Create a 10 pixel box to write into
            epd.text(str(i), text_row, text_column, 0x00)               # Write the information in as an inverse/negative
            epd.displayPartial(epd.buffer)
    else:
        # Write the array information
        if isinstance(optional_array, list):
            # Determin longest string in the array list
            longest_string = max(optional_array, key=len)
            num_char = len(longest_string)

            # Display the Array Items in the Partial Location
            for array_string in optional_array:
                epd.fill_rect(text_row-1, text_column-1, num_char*pixel_per_char, 10, 0xff)    # Prepare space for all strings (start row, start col, pixels_in_row, pixels_in_col, color_in_amount)
                epd.text(array_string, text_row, text_column, 0x00)
                epd.displayPartial(epd.buffer)
        else:
            print("Unknown Optional Array:\t".format(optional_array))

# Function for Setting E-Ink Display to Sleep
def sleep_display(epd):
    print("[*] Setting E-Ink Display to Deep Sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()

# Function for Performing Signature E-Ink Test
def run_signature_check(epd):
    # Variables
    version_number = 1.0
    header_string = "-=[ Mauddib28's Bluetooth Low Energy GATT ]=-"
    implement_string = " - Pico W Implementation - "
    value_string = "Value: "
    value_array = ["Read I/O", "Write I/O", "Notifications", "BLEEP Testing", "Version {0}".format(str(version_number))]
    start_line = 10
    bottom_line = 120
    partial_row = 60
    partial_col = 120
    wait_time_ms = 2000

    # Initialize and "Wipe" the Display
    epd.fill(0xFF)

    # Creating Base Display Template
    set_display_template(epd, header_string, implement_string, value_string, start_line, bottom_line)
    # Set the Display with the Template
    epd.Display_Base(epd.buffer)
    epd.delay_ms(wait_time_ms)

    if dbg:    
        # Creating Partial Display Information
        set_partial_display(epd, partial_row, partial_col, optional_array=10)   

    # Second Partial Display Information
    set_partial_display(epd, partial_row, partial_col, value_array)

    # Clear Screen and Sleep
    sleep_display(epd)

## Main Code

# Test Display Function
def test_display():
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()
    
    epd.fill(0xff)
    epd.text("Waveshare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 20, 0x00)
    epd.text("Raspberry Pico", 0, 30, 0x00)
    epd.text("Hello World", 0, 40, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.vline(5, 55, 60, 0x00)
    epd.vline(100, 55, 60, 0x00)
    epd.hline(5, 55, 95, 0x00)
    epd.hline(5, 115, 95, 0x00)
    epd.line(5, 55, 100, 115, 0x00)
    epd.line(100, 55, 5, 115, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.rect(130, 10, 40, 80, 0x00)
    epd.fill_rect(190, 10, 40, 80, 0x00)
    epd.Display_Base(epd.buffer)
    epd.delay_ms(2000)
    
    epd.init()
    for i in range(0, 10):
        epd.fill_rect(175, 105, 10, 10, 0xff)
        epd.text(str(i), 177, 106, 0x00)
        epd.displayPartial(epd.buffer)
        
    print("sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()
    
    
    
    epd = EPD_2in13_V4_Portrait()
    epd.Clear()
    
    epd.fill(0xff)
    epd.text("Waveshare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 30, 0x00)
    epd.text("Raspberry Pico", 0, 50, 0x00)
    epd.text("Hello World", 0, 70, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.vline(10, 90, 60, 0x00)
    epd.vline(90, 90, 60, 0x00)
    epd.hline(10, 90, 80, 0x00)
    epd.hline(10, 150, 80, 0x00)
    epd.line(10, 90, 90, 150, 0x00)
    epd.line(90, 90, 10, 150, 0x00)
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    
    epd.rect(10, 180, 50, 40, 0x00)
    epd.fill_rect(60, 180, 50, 40, 0x00)
    epd.Display_Base(epd.buffer)
    epd.delay_ms(2000)
    
    epd.init()
    for i in range(0, 10):
        epd.fill_rect(40, 230, 40, 10, 0xff)
        epd.text(str(i), 60, 230, 0x00)
        epd.displayPartial(epd.buffer)
        
    print("sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()


'''
Notes For Format Testing:
    - Number of Characters Across Appears to be approximately 30
    - Number of Vertical Characteristics Appears to Place 120 as the bottom "Row"
'''
# Formatted Display Demo
def format_display_demo():
    print("[*] Testing Formatted Display Functionality")

    # Initialize the E-Ink Display
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()

    # Variable Defitions
    header_string = "-=[ Mauddib28's Bluetooth Low Energy GATT ]=-"
    implement_string = " - Pico W Implementation - "
    current_line = 10
    bottom_line = 120

    # Internal Function for Chunking a String
    def chunkstring(string, length):
        return (string[0+i:length+i] for i in range (0, len(string), length))

    # Internal Function to Write Text is set Lengths
    def fit_text(epd, text_string, current_line):
        # Internal Variables
        curr_line = current_line
        width_limit = 30

        for chunk in chunkstring(text_string, width_limit):
            print("Chunk:\t".format(chunk))
            epd.text(chunk, 0, curr_line, 0x00)
            curr_line += 20

        # Return the line now on
        return curr_line
    
    # Debugging
    if dbg:
        fields = list(chunkstring(header_string, 30))
        print(fields)

    # Create a Base Template for the E-Ink Display
    epd.fill(0xFF)          # Not sure why, but this is apparently part of how/what is being written
    #epd.text(header_string, 0, 10, 0x00)        # Writing is making white space?
    #epd.text(implement_string, 0, 30, 0x00)     #   - Might be what the 0x00 aspect is for
    #epd.rect(10, 180, 50, 40, 0x00)
    #epd.vline(10, 180, 60, 0x00)
    #epd.hline(10, 90, 60, 0x00)
    current_line = fit_text(epd, header_string, current_line)
    current_line = fit_text(epd, implement_string, current_line)

    # Test Placement for a Read/Write/Value Field
    epd.text("Value: ", 0, bottom_line, 0x00)

    # Add the template as a Base to the Image
    epd.Display_Base(epd.buffer)
    epd.delay_ms(2000)

    # Perform the Partial Updates into the Base Template
    epd.init()
    for i in range(0, 10):
        epd.fill_rect(59, 119, 10, 10, 0xff)
        epd.text(str(i), 60, 120, 0x00)
        epd.displayPartial(epd.buffer)

    # Clear the final display
    print("[*] Screen to Sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()

# Demoing Signature E-Ink Testing
def demo_sig():
    print("[*] Starting Signature Test")

    # Initialize Display
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()

    # Call Signature Function
    run_signature_check(epd)

    print("[+] Completed Signature Test")

# Demo Function
def demo():
    print("[*] Starting E-ink Display Demo")
    
    # Initialize display with verification
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()
    #if not epd.init():
    #    print("[-] Display initialization failed!")
    #    return
        
    # Test pattern
    print("[*] Drawing test pattern...")
    epd.fill(0xFF)  # White background
    #epd.rect(0, 0, EPD_WIDTH, EPD_HEIGHT, 0)  # Black border
    #epd.text("Display Test", 10, 10, 0)
    epd.text("WaveShare", 0, 10, 0x00)
    epd.text("ePaper-2.13_V4", 0, 30, 0x00)
    epd.text("Raspberry Pico WH", 0, 50, 0x00)
    epd.text("Bluetooth Low Energy", 0, 70, 0x00)
    epd.text("   GATT Server", 0, 80, 0x00)
    #epd.display_frame()
    epd.display(epd.buffer)
    epd.delay_ms(2000)

    # Sleep the Display
    print("E-Ink Sleep")
    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()     # Causes a deep-sleep state
    
    print("[*] Starting BLE service...")
    ble = bluetooth.BLE()
    ble_display = BLEEinkDisplay(ble, epd)
    
    # Onboard LED for status
    led = Pin("LED", Pin.OUT)
    
    print("[+] Ready for connections")
    #epd.display_text("Ready for\nBLE connections")
    epd.display_text("Ready for BLE")
    
    try:
        while True:
            if ble_display._connections:
                led.toggle()  # Blink when connected
            else:
                led.off()
            time.sleep_ms(500)
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        epd.Clear()
        ble.active(False)

# Function for Running BLE GATT Server
def ble_eink_server():
    print("[*] Starting E-ink Display Demo")
    
    # Initialize display with verification
    epd = EPD_2in13_V4_Landscape()
    epd.Clear()

    # Print the signature screen
    run_signature_check(epd)        

    # Start the Main Service 
    print("[*] Starting BLE service...")
    ble = bluetooth.BLE()
    ble_display = BLEEinkDisplay(ble, epd)
    
    # Onboard LED for status
    led = Pin("LED", Pin.OUT)
    
    print("[+] Ready for connections")
    #epd.display_text("Ready for\nBLE connections")
    #epd.display_text("Ready for BLE")       # Note: Not sure this does anything
    epd.init()
    epd.fill(0xFF)
    ready_string = "Ready for BLE Connections!"
    ready_string2 = "Time to Learn!"
    fit_text(epd, ready_string, 10, 30)
    fit_text(epd, ready_string2, 20, 30)
    #epd.display_text("Ready for BLE Connections!\nTime to Learn!")
    epd.display(epd.buffer)
    epd.delay_ms(2000)
    epd.Clear()
    #sleep_display(epd)
    
    try:
        while True:
            if ble_display._connections:
                led.toggle()  # Blink when connected
            else:
                led.off()
            time.sleep_ms(500)
            
    except KeyboardInterrupt:
        print("\n[-] Stopping demo")
        epd.Clear()
        ble.active(False)

if __name__ == "__main__":
    print("[*] Starting E-ink Display BLE Demo")
    #demo() 
    #test_display()
    #format_display_demo()
    #demo_sig()
    ble_eink_server()