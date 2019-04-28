# Starting your First Scan

## Setup

Make sure that you at least set up the oscilloscope, connect it to the
microphone, and have verified that the 3D printer moves.

## Scanning

I find it easiest to start scanning using an interactive terminal, preferably
using `ipython`.
Go to the top level directory (the folder `scanning-microphone`), and start
the interactive terminal.

```bash
ipython
```

Then, make sure you get what serial the 3D printer is connected to (which you should have gotten during the setup stage) and put that as the argument to `serial` when initializing the scanner.

```python
>>> from scanner import Scanner
>>> scanner = Scanner(serial="/dev/ttyACM0")
```

Try to move the scanner to the appropriate starting location of the scan.

```python
>>> scanner.move_speed(x=-10, y=-10, z=-5, speed=5000)
```

The units for x, y, z are millimeters, and the speed is in units of mm/min.
Make sure that you orient yourself since there are no bounds checking - you'll just wear out the motors if you attempt to go out of bounds.
This is by default a blocking command, and you only regain use of the python program when it finishes.
If you want a nonblocking version (useful if you want to be collecting audio samples while the 3d printer is moving) then you can also use the function `move_speed_noblock` with the same arguments.

Once you have moved the microphone head to the correct location, you can do a scan.
Read the comments 




## Troubleshooting

### Errno 16 Resource Busy

If you get this error:

![doubleconnection](../images/scanning/doubleconnectionerror.png)

most likely what has happened is that you have another process that is already connected to the scanner.
Check if you have some other terminal open that is connected to the scanner.
Or, you can just kill all other python processes to make sure.

```bash
sudo pkill -9 python
```

Then, try to reconnect to the scanner, and it should work properly.





