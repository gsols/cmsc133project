; The delay counter will be managed by DEC instruction on a register.

; --- Register Definitions (2-bit encoding) ---
.EQU R0, 00b ; General purpose register
.EQU R1, 01b ; General purpose register
.EQU R2, 10b ; General purpose register
.EQU R3, 11b ; General purpose register

; --- Program Code (designed to fit 16 instructions for 4-bit PC) ---
; Machine Code Format: [Opcode (4-bit)][Operand (4-bit)]

; Memory Address: 0000b
START:
    ; Initialize System: Turn off light
    LDI R0, #0000b          ; R0 = 0 (Value for OFF)
    OUT R0, LIGHT_PORT      ; Turn OFF Light (Port 00b)

; Memory Address: 0010b
WAIT_MOTION:
    ; Monitor Motion Sensor: Loop until motion is detected
    IN R1, MOTION_PORT      ; Read motion sensor status into R1 (Port 01b)
    MOV R0, R1              ; Copy R1 to R0 to test its value. (R0 will become R1)
    ; Note: MOV R0,R1 does NOT set Z-flag directly. SUB is needed for Z-flag.
    ; This is a crucial point for 16-instruction limit.
    ; Without an explicit 'TEST' or 'CMP' instruction that sets Z-flag on IN or MOV,
    ; a SUB instruction is needed.

    SUB R0, R0              ; Rd=Rd-Rs => R0=R0-R0. This is just to set Z_flag based on R0's (which holds R1's) value.
                            ; If R0 (motion sensor) is 0, Z_flag will be 1.
    JZ WAIT_MOTION          ; If Z_flag is set (no motion), loop back

; Memory Address: 0110b
MOTION_DETECTED:
    ; Motion Detected: Load delay value, turn on light
    LDI R2, #1000b          ; R2 = 8 (Example delay value. Assuming 4-bit immediate for LDI)
                            ; This sets a delay of 8 'ticks'. Each tick is one DEC instruction.
    LDI R0, #0001b          ; R0 = 1 (Value for ON)
    OUT R0, LIGHT_PORT      ; Turn ON Light (Port 00b)

; Memory Address: 1001b
COUNTDOWN_LOOP:
    ; Countdown Delay
    DEC R2                  ; Decrement R2 (delay register). Sets Z_flag if R2 becomes 0.
    JZ LIGHT_OFF            ; If Z_flag is set (delay expired), jump to turn off light
    JMP COUNTDOWN_LOOP      ; Else, continue countdown

; Memory Address: 1100b
LIGHT_OFF:
    ; Delay Expired: Turn off light
    LDI R0, #0000b          ; R0 = 0 (Value for OFF)
    OUT R0, LIGHT_PORT      ; Turn OFF Light (Port 00b)
    JMP START               ; Go back to initial state (waiting for motion)

; Total Instructions: 15
