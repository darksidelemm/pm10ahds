import logging
import sys
import serial


class PM10AHDS(object):
    """
    A class to communicate with a Power-Made PM10AHDS Power Meter
    """

    def __init__(self, port, address=1, baud_rate=9600, timeout=2):
        """
        Create a PM10AHDS Communication Object.
        """


        if (address < 1) or (address>254):
            raise ValueError("Address must be within range 1 - 254")
        else:
            self.address = address

        # Connect
        logging.info(f"Attempting to connect to a PM10AHDS on {port}, at {baud_rate} baud...")
        try:
            self.s = serial.Serial(port, baud_rate, timeout=timeout)
        except Exception as e:
            logging.critical("Could not open serial port - %s" % str(e))
            return None

    def __del__(self):
        try:
            self.s.close()
        except AttributeError:
            # Silently handle errors if self.s does not exist.
            pass

    def construct_packet(self, command):
        """
        Construct a packet to be sent to the PowerMate.

        Packet format is:
        <AA<command>;CCCC\n
        Where:
        < = 'Start of message'
        AA = PowerMate address (hexadecimal, 01-FE)
        <command> = Command to send. Usually a letter followed by comma-separated values
        ; = Separator
        CCCC = Checksum, a modulo-65536 sum of the address and command bytes.
        """

        if type(command) != bytes:
            command = command.encode()

        # Generate the address as a one byte of hex
        _address = f"{self.address:02x}".upper().encode()

        # Generate the packet body which the checksum will be calculated over
        _body = _address + command
        # Calculate the checksum, which is just a modulo-65536 sum of the packet body
        _checksum = f"{sum(list(bytearray(_body)))%65536:04x}".upper().encode()

        # Construct the packet: SOM+body+;+checksum+CRLF
        _packet = b'<' + _body + b';' + _checksum + b'\r\n'

        return _packet

    def validate_packet(self, packet):
        """
        Validate the modulo-65536 checksum (and other parts..) in a response packet
        e.g.: b'>01S,0,0,12627447,89716830841,3200,244535000,32400,1,404360,7927;0C74'
        """

        # Check for correct SOM, which should be a > character
        if packet[0] != 62:
            logging.error("Packet Validation - Did not find correct SOM.")
            return False
        
        # Check the address matches
        if packet[1:3] != f"{self.address:02x}".upper().encode():
            logging.error(f"Packet Validation - Address {packet[1:3]} did not match expected address ({self.address:02x}).")
            return False

        # Now try and calculate the checksum..
        try:
            _checksum = packet.split(b';')[1]
            _body = packet.split(b';')[0]
        except:
            logging.error("Packet Validation - Could not extract checksum portion of packet.")
            return False
        
        _calculated_checksum = f"{sum(list(bytearray(_body[1:])))%65536:04x}".upper().encode()

        if _checksum != _calculated_checksum:
            logging.error(f"Packet Validation - Calculated Checksum ({_calculated_checksum}) does not match supplied checksum ({_checksum}).")
            return False
        else:
            return True

    def request_status(self):
        """
        Request the latest status from the Power-Mate.
        Returns a dictionary with status data, or None if the packet could not be decoded correctly.
        """

        # Status request command: S,
        _packet = self.construct_packet(b'S,')

        logging.debug(f"Sending Status Request: {_packet}")

        # Clear any messages in the serial buffer, the send the packet
        self.s.flush()
        self.s.write(_packet)

        # Wait for a response - this can take up to a second!
        _resp = self.s.readline()
        logging.debug(f"Status Response: {_resp}")

        if _resp == b'' or _resp == None:
            logging.error("No response from PowerMate!")
            return None

        # Remove any line endings
        _resp = _resp.strip()

        # Check the packet for validity (correct structure, address, checksum)
        if self.validate_packet(_resp):
            # Get body part of packet and convert it back to a string
            _body = _resp.split(b';')[0].decode()

            if _body[3] != 'S':
                logging.error("Not a status response!")
                return None
            
            _fields = _body.split(',')

            if len(_fields) != 11:
                logging.error("Not enough fields in status response!")
                return None

            # Extract all the fields and convert them to useful units
            output = {}
            output['runtime_seconds'] = int(_fields[3])
            # Energy is provided in MilliJoules - convert to kWh
            output['energy_kwh'] = int(_fields[4])*2.7777777777778E-10
            # Power is provided in Milliwatts - convert to Watts
            output['power_w'] = int(_fields[5]) / 1e3
            # Voltage is provided in microvolts (?!) - convert to Volts
            output['voltage_v'] = int(_fields[6]) / 1e6
            # Current is provided in microamps (?!?!) - convert to Amps
            output['current_a'] = int(_fields[7]) / 1e6
            # Power Factor Lead/Lag
            if _fields[8] == '1':
                output['powerfactor_leadlag'] = 'lag'
            else:
                output['powerfactor_leadlag'] = 'lead'
            # Power Factor
            output['powerfactor'] = int(_fields[9]) / 1e6
            # Apparent Power is provided in milli-va - convert to VA
            output['apparent_power_va'] = int(_fields[10]) / 1e3

            return output

        
        else:
            return None

    def request_erase(self):
        """
        Requests an erase of the Power-Mate's registers
        """

        # Status request command: S,
        _packet = self.construct_packet(b'E,')

        logging.debug(f"Sending Erase Request: {_packet}")

        # Clear any messages in the serial buffer, the send the packet
        self.s.flush()
        self.s.write(_packet)

        # Wait for a response - this can take up to a second!
        _resp = self.s.readline()
        logging.debug(f"Erase Response: {_resp}")

        if _resp == b'' or _resp == None:
            logging.error("No response from PowerMate!")
            return None

        # Remove any line endings
        _resp = _resp.strip().decode()

        if _resp[3] == 'E':
            return True
        else:
            logging.error("Unknown response to Erase request!")
            return False


    def close(self):
        self.s.close()


if __name__ == "__main__":
    """
    Basic test script. Connect to a PM10AHDS and query it for some status.
    """
    import sys
    from pprint import pprint

    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
    )

    def print_data(data):
        print(data)

    if len(sys.argv) > 1:
        _port = sys.argv[1]
    else:
        print("Usage: python PM10AHDS.py <serial_port>")
        sys.exit(1)

    power_meter = PM10AHDS(_port)

    pprint(power_meter.request_status())

    power_meter.close()



    