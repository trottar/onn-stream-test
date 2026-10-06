# E2-S1 — the SNES question (pre-registered §4)

## E1-SNES-STREAM/run1

- RetroArch 59.993 fps; capture 60.024 fps; encoder dup+drop 0.10/min; rendered 59.659 fps; video loss 49.1/min.
- RetroArch 436.3 % of a core over 27 threads; encoder 28.0 %; busiest core p95 54.7 %; busiest-per-second p95 57.7 %; PSI cpu 45.3 ms/s.
- RetroArch's busiest threads (% of a core, mean / p95; policy; syscall mode): 37.4 / 44.0 (0, 202); 37.4 / 43.8 (0, running); 37.4 / 44.0 (0, 202); 37.4 / 43.0 (0, running); 37.3 / 43.0 (0, 202); 37.3 / 43.0 (0, 202).
- Encoder's busiest threads: 3.6 / 4.0; 1.8 / 2.0; 1.8 / 2.0; 1.8 / 2.0.
- Rendered fps per minute: [58.97, 59.23, 59.24, 59.23, 59.58, 59.55, 59.42, 59.66, 59.64, 59.73, 59.84, 59.91, 59.91, 59.87, 59.9, 59.93, 59.89, 59.82, 59.86, 59.99]
- Capture fps per minute: [60.01, 60.0, 59.99, 59.99, 60.01, 60.0, 59.99, 60.01, 60.0, 59.99, 60.0, 59.99, 60.01, 60.01, 59.99, 59.98, 60.5, 59.5, 60.51, 59.99]
- **Reading (pre-registered): the emulator's load starves the capture/encoder.**

## E1-SNES-STREAM/run2

- RetroArch 59.999 fps; capture 59.999 fps; encoder dup+drop 0.10/min; rendered 59.978 fps; video loss 2.5/min.
- RetroArch 516.5 % of a core over 27 threads; encoder 20.6 %; busiest core p95 62.5 %; busiest-per-second p95 62.9 %; PSI cpu 103.0 ms/s.
- RetroArch's busiest threads (% of a core, mean / p95; policy; syscall mode): 44.1 / 47.0 (0, running); 44.1 / 47.1 (0, running); 44.0 / 47.1 (0, running); 44.0 / 47.0 (0, running); 44.0 / 47.1 (0, running); 44.0 / 47.0 (0, running).
- Encoder's busiest threads: 2.8 / 4.0; 1.3 / 2.0; 1.3 / 2.0; 1.3 / 2.0.
- Rendered fps per minute: [59.9, 59.99, 59.97, 60.03, 59.99, 59.92, 59.87, 59.97, 60.0, 59.99, 60.03, 60.01, 59.99, 60.02, 60.0, 59.93, 60.03, 59.99, 60.01, 59.94]
- Capture fps per minute: [60.02, 60.0, 60.01, 59.99, 59.98, 59.98, 59.99, 60.01, 60.0, 60.0, 60.01, 59.98, 60.0, 60.03, 59.99, 60.0, 59.99, 60.0, 59.98, 60.0]
- **Reading (pre-registered): the emulator's load starves the capture/encoder.**

