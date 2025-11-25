# This class provides a Python API to control the Robotiq 2F-85 gripper
# using the TCP/IP protocol.

# Copyright (c) 2025 Annie Huang, Jiacheng Li. All rights reserved.

import socket
import time
import warnings
import atexit

class Gripper_Interface:
    """
    A class to control a Robotiq 2F-85 gripper via a TCP/IP socket.

    GET/SET Parameter Reference:
      - ACT: Activate gripper (1 = activate, 0 = reset).
      - GTO: Go To command, performs the move with the last set parameters.
      - FOR: Force setting (0-255).
      - SPE: Speed setting (0-255).
      - POS: Position setting (0-255, where 0 is fully open).

    Status Parameter Reference:
      - STA: Gripper status (0 = reset, 1 = activating, 3 = active).
      - PRE: Position Request, an echo of the last commanded position.
      - OBJ: Object detection status (0 = moving, 1 = stopped opening, 
             2 = stopped closing, 3 = at rest, no object).
    """

    def __init__(self, ip: str = '172.22.22.2', port: int = 63352, auto_init: bool = True):
        """
        Initializes the GripperInterface object.
        Args:
            ip (str): The IP address of the gripper controller.
            port (int): The port number for the TCP/IP connection.
            auto_init (bool): If True, automatically connects to and activates
                              the gripper upon instantiation.
        """
        self._ip = ip
        self._port = port
        self._auto_init = auto_init
        self._show_warnings = True
        self._client_socket = None

        if self._auto_init:
            try:
                self.connect()
                self.SET("POS", 0)
                self.activate()
            except Exception as e:
                print(f"Error during auto-initialization: {e}")
                self.disconnect()
        else:
            self._show_warnings = False
            
    def connect(self):
        """
        Establishes the TCP/IP connection to the gripper.
        """
        if self._client_socket:
            return
        try:
            self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client_socket.settimeout(5.0)
            self._client_socket.connect((self._ip, self._port))
            atexit.register(self.disconnect)
            time.sleep(0.2)
        except (socket.timeout, ConnectionRefusedError) as e:
            self._client_socket = None
            raise ConnectionError(f"Failed to connect to gripper")

    def disconnect(self):
        """
        Closes the TCP/IP connection. This method is safe to call multiple times.
        """
        if self._client_socket:
            self._client_socket.close()
            self._client_socket = None

    def _send_command(self, command: str):
        """Internal helper to send a command string to the gripper."""
        if not self._client_socket:
            raise ConnectionError("Gripper is not connected.")
        self._client_socket.sendall(command.encode('ascii'))
        time.sleep(0.05) 

    def _read_response(self) -> str:
        """Internal helper to read a response line from the gripper."""
        if not self._client_socket:
            raise ConnectionError("Gripper is not connected.")
        
        buffer = b''
        while True:
            try:
                chunk = self._client_socket.recv(1024)
                if not chunk:
                    raise ConnectionError("Connection lost while reading response.")
                buffer += chunk
                if b'\n' in buffer:
                    response, _, buffer = buffer.partition(b'\n')
                    return response.decode('ascii').strip()
            except socket.timeout:
                raise TimeoutError("Timed out waiting for a response from the gripper.")

    def SET(self, var: str, val: int):
        """
        Sends a 'SET' command to the gripper.

        Args:
            var (str): The parameter to set (e.g., "POS", "SPE", "FOR").
            val (int): The value to set (typically 0-255).
        """
        command = f"SET {var.upper()} {int(val)}\n"
        self._send_command(command)

    def GET(self, var: str) -> int:
        """
        Sends a 'GET' command and returns the gripper's response.

        Args:
            var (str): The parameter to get (e.g., "POS", "STA", "OBJ").

        Returns:
            int: The integer value returned by the gripper.
        """
        command = f"GET {var.upper()}\n"
        self._send_command(command)
        response = self._read_response()
        
        parts = response.split()
        # The response is typically 'VAR val', e.g., 'pos 123'
        # to be tested about matching, there might be multiple ack
        if len(parts) < 2: # loose condition
            raise ValueError(f"Unexpected response from gripper: '{response}'")
        
        return int(parts[1])

    def reset(self):
        """
        Resets the gripper. Deactivates it and waits for confirmation.
        """
        self.SET("ACT", 0)
        while self.GET("ACT") != 0 or self.GET("STA") != 0:
            self.SET("ACT", 0)
            time.sleep(0.1)
        time.sleep(0.5)

    def activate(self):
        """
        Activates the gripper. If not already active, it will reset first.
        """
        if self.GET("STA") == 3:
            return
            
        self.reset()
        
        self.SET("ACT", 1)
        time.sleep(1.0)

        start_time = time.time()
        while self.GET("STA") != 3:
            if time.time() - start_time > 10: # 10-second timeout
                raise TimeoutError("Gripper activation timed out.")
            time.sleep(0.1)
        
        time.sleep(0.5)

    def move(self, position: int, speed: int = None, force: int = None, block: bool = True) -> int:
        """
        Moves the gripper to a specified position.

        Args:
            position (int): Target position (0-255). 0 is open, 255 is closed.
            speed (int, optional): Movement speed (0-255). Defaults to last setting.
            force (int, optional): Movement force (0-255). Defaults to last setting.
            block (bool): If True, the function will wait until the move is
                          complete. If False, it returns immediately.

        Returns:
            int: The final position of the gripper after the move command.
        """
        if speed is not None:
            speed = min(max(speed, 0), 255)
            self.SET("SPE", speed)
            if self._show_warnings and speed != 0:
                warnings.warn("Gripper Speed has been set. Please confirm this is intended.")

        if force is not None:
            force = min(max(force, 0), 255)
            self.SET("FOR", force)
            if self._show_warnings and force != 0:
                warnings.warn("Gripper Force has been set. Please confirm this is intended.")
        
        position = min(max(position, 0), 255)

        # Set target position and issue the "Go To" command
        self.SET("POS", position)
        self.SET("GTO", 1)

        # Wait for the gripper to acknowledge the new target position
        while self.GET("PRE") != position:
            time.sleep(0.01)

        # If blocking, wait for the move to finish
        if block:
            while self.GET("OBJ") == 0: # 0 means 'moving'
                time.sleep(0.01)
        
        # Return the final measured position
        return self.GET("POS")

    def grip(self, block: bool = True) -> int:
        """
        Closes the gripper fully (grips).

        Args:
            block (bool): If True, waits for the grip action to complete.

        Returns:
            int: The final position of the gripper.
        """
        return self.move(position=255, block=block)

    def release(self, block: bool = True) -> int:
        """
        Opens the gripper fully (releases).

        Args:
            block (bool): If True, waits for the release action to complete.

        Returns:
            int: The final position of the gripper.
        """
        return self.move(position=0, block=block)

    def get_pos(self) -> int:
        """Convenience method to get the current gripper position."""
        return self.GET("POS")


if __name__ == '__main__':
    # It's recommended to use a 'with' statement to ensure the connection
    # is automatically closed even if errors occur.
    
    # Replace with your gripper's actual IP if different
    GRIPPER_IP = "172.22.22.2" 
    
    print("--- Example: Using 'with' statement (recommended) ---")
    try:
        gripper = Gripper_Interface()
        print(f"Initial Position: {gripper.get_pos()}")

        time.sleep(1)

        final_pos = gripper.grip()
        print(f"Gripping complete. Final position: {final_pos}")
        
        time.sleep(2)
        
        # Release the object
        final_pos = gripper.release()
        print(f"Releasing complete. Final position: {final_pos}")

    except (ConnectionError, TimeoutError, ValueError) as e:
        print(f"\nAn error occurred: {e}")
        print("Please check the gripper connection and IP address.")
