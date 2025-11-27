# Robotiq-Gripper-Interface
TCP/IP-based Gripper Interface for MATLAB and Python.
Tested on **Robotiq 2F-85** at JHU Wyman.

An alternative to deprecated ROS packages, allowing for direct control via scripts without interacting with the teaching pendant, and seamless integration into existing MATLAB/Python pipelines.

## Setup
<code>URCap</code> for Robotiq gripper must be installed on the teaching pendant. Note: While [Official URCap](https://robotiq.com/support) requirements are strict, I found the URCap to be compatible with some earlier Polyscope versions than stated.

For power supply and wiring, please strictly follow the [Official Manual](https://blog.robotiq.com/hubfs/support-files/2F-85_2F-140_UR_PDF_20240402.pdf).


## Quick Start
Most example will be written in MATLAB but usage in python is the same.
```matlab
% Initialization (automatically performs activation)
gp = Gripper_Interface('192.168.1.100'); 

% Basic actions
gp.grip();      % Full close (default force/speed)
gp.release();   % Full open
```
### Core methods
| Method | Description |
| :--- | :--- |
| `connect()` | Establish TCP connection with the gripper. |
| `disconnect()` | End the connection. |
| `activate()` | Activate the gripper (Required before any motion). |
| `reset()` | Reset gripper state. Upon completion, gripper will be inactive. |
| `grip(Block)` | Close gripper. If `Block=1` (default), blocks thread until action is complete. |
| `release(Block)` | Open gripper. If `Block=1` (default), blocks thread until action is complete. |
| `move(Pos, Speed, Force)` | Actuate gripper to target `Pos` with specific `Speed` and `Force`. All values are in 0-255. |
| `get_pos()` | Returns current position sensor reading (0-255). |
| `SET(CMD, VAL)` | Set property value of a register `CMD` (string) to `VAL` (0-255). |
| `GET(CMD)` | Return the property value for corresponding `CMD`. |

### Available Properties (CMD)
<code>R/W</code> means this property can be used in both <code>SET</code> and <code>GET</code>.

<code>Read</code> means this property can be used in <code>GET</code>.

| CMD | Access | Description |
| :---: | :---: | :--- |
| **ACT** | R/W | **Activation bit.** <br>0 = Deactivated<br>1 = Activated |
| **GTO** | R/W | **Go To action.** <br>1 = Move to requested position<br>0 = Stop/Stay at current position |
| **ATR** | R/W | **Automatic Release Routine.** (Emergency slow move/release). |
| **FOR** | R/W | **Force.** (0-255) |
| **SPE** | R/W | **Speed.** (0-255) |
| **POS** | R/W | **Position.** (0-255) <br>0 = Fully Open |
| **STA** | Read | **Status.** <br>0 = Reset<br>1 = Activating<br>3 = Active |
| **PRE** | Read | **Position Request Echo.** Record of last commanded position. |
| **OBJ** | Read | **Object Detection Status.** <br>**0**: Moving to position (No object detected).<br>**1**: Contact while **opening** (Object detected).<br>**2**: Contact while **closing** (Object detected).<br>**3**: Reached position (No object detected / Object dropped). |


## References
[official manual](https://blog.robotiq.com/hubfs/support-files/2F-85_2F-140_UR_PDF_20240402.pdf).

[UR forum](https://dof.robotiq.com/discussion/2420#Comment_7296)
