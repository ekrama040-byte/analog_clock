# Functional Analog Clock

A real-time analog clock implemented with Python 3 and the built-in `turtle` graphics module. It displays a numbered face, hour/minute/second hands, and a digital readout.

## Requirements

- Python 3
- A desktop environment that supports Python Turtle/Tk graphics

No third-party Python packages are needed.

## Run

From a terminal opened in this project folder:

```powershell
python analog_clock.py
```

Close the graphics window to exit.
On Windows, the clock automatically saves a screenshot to `analog_clock_screenshot.png` about one second after it opens.

## Design

- `draw_face()` draws the dial, all 60 minute marks, stronger hour marks, and 1–12 labels.
- `draw_hand()` clears and redraws a hand around the shared center.
- `update_clock()` reads the local system time and is rescheduled with `screen.ontimer()` at 100 ms intervals.
- The hour hand includes elapsed minutes and seconds, and the minute hand includes elapsed seconds.
- The digital readout displays the local time and the full date below the dial.
- Press `Space` or `P` to pause/resume the clock. Pausing freezes both the hands and readout.
- Clock angles are measured from 12 o'clock; they are converted to Turtle headings as `90 - angle`.
