# E4-S1 — the SNES row read by E2 §4 (reported; Snes9x)

## E1-SNES-STREAM/run1

- RetroArch 59.999 fps; capture 59.017 fps; encoder dup+drop 59.98/min; rendered 58.738 fps; video loss 54.0/min.
- RetroArch 8.3 % of a core over 17 threads; encoder 27.0 %; busiest core p95 16.5 %; busiest-per-second p95 18.3 %; PSI cpu 11.0 ms/s.
- RetroArch's busiest threads (% of a core, mean / p95; policy; syscall mode): 7.2 / 8.0 (0, 7); 0.4 / 1.0 (0, 7); 0.4 / 1.0 (0, 202); 0.4 / 1.0 (0, 202); 0.0 / 0.0 (0, 202); 0.0 / 0.0 (0, 202).
- Encoder's busiest threads: 3.0 / 4.0; 1.8 / 2.0; 1.8 / 2.0; 1.8 / 2.0.
- Rendered fps per minute: [58.86, 58.78, 58.76, 58.77, 58.61, 58.79, 58.84, 58.65, 58.8, 58.96, 58.86, 58.86, 58.83, 58.61, 58.72, 58.96, 58.8, 58.75, 58.36, 58.28]
- Capture fps per minute: [58.99, 58.99, 58.98, 59.0, 59.0, 59.49, 59.01, 58.99, 58.99, 58.99, 58.98, 58.99, 58.99, 58.99, 59.0, 58.99, 58.98, 59.0, 58.99, 58.99]
- **Reading (pre-registered): the emulator's load starves the capture/encoder.**

