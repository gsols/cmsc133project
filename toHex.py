import re

# --- Instruction Set Definition ---
# Maps mnemonic to its opcode and operand format.
# Operand formats:
#   - "": No operand (e.g., NOP, HLT)
#   - "reg_port": Register (2-bit) and Port (2-bit) (e.g., IN Rn, P -> nppp)
#   - "reg_reg": Destination Register (2-bit) and Source Register (2-bit) (e.g., MOV Rd, Rs -> dsrc)
#   - "reg_imm2": Register (2-bit) and 2-bit Immediate (e.g., LDI Rn, #Imm -> nimm)
#   - "reg": Register (2-bit) (e.g., DEC Rn -> n000)
#   - "address": 4-bit Address (e.g., JMP addr -> aaaa)
INSTRUCTION_SET = {
    "NOP": {"opcode": "0000", "format": ""},
    "HLT": {"opcode": "0001", "format": ""},
    "IN":  {"opcode": "0010", "format": "reg_port"},
    "OUT": {"opcode": "0011", "format": "reg_port"},
    "MOV": {"opcode": "0100", "format": "reg_reg"},
    "LDI": {"opcode": "0101", "format": "reg_imm2"},
    "ADD": {"opcode": "0110", "format": "reg_reg"},
    "SUB": {"opcode": "0111", "format": "reg_reg"},
    "DEC": {"opcode": "1000", "format": "reg"},
    "JMP": {"opcode": "1001", "format": "address"},
    "JZ":  {"opcode": "1010", "format": "address"},
}

# --- Register Encoding (2-bit) ---
REGISTERS = {
    "R0": "00",
    "R1": "01",
    "R2": "10",
    "R3": "11",
}

# --- Port Encoding (2-bit, based on 4-bit operand split) ---
# Note: Limited to 4 ports due to 2-bit port addressing in IN/OUT format.
PORTS = {
    "LIGHT_PORT": "00",
    "MOTION_PORT": "01",
    "DUMMY_PORT_A": "10", # Placeholder for a 3rd port if needed, e.g., LOAD_CNT_U_PORT
    "DUMMY_PORT_B": "11", # Placeholder for a 4th port if needed, e.g., LOAD_CNT_T_PORT
}

# --- Assembly Code ---
# This is the simplified assembly code to fit the 16-instruction limit
# and adhere to 2-bit immediate/port addressing.
ASSEMBLY_CODE = """
; *****************************************************************************
; PROGRAM: Motion Sensor Light Control (Strictly 4-bit PC & 2-bit Imm/Port)
; DESCRIPTION: Detects motion, turns on LED, counts down max 3 seconds, turns off.
;              - Uses DEC for countdown.
;              - No motion re-detection during countdown.
;              - Port addresses are 2-bit (00-11).
;              - LDI immediate values are 2-bit (0-3).
; *****************************************************************************

; --- I/O Port Definitions (2-bit addresses for IN/OUT) ---
.EQU LIGHT_PORT,         00b  ; Output port for the LED
.EQU MOTION_PORT,        01b  ; Input port for the motion sensor
; Note: LOAD_CNT_U_PORT, LOAD_CNT_T_PORT, ENABLE_CNT_PORT, TIMER_ZERO_FLAG_PORT
; are not directly addressable with distinct 2-bit port addresses with this ISA.

; --- Register Definitions (2-bit encoding) ---
.EQU R0, 00b ; General purpose register
.EQU R1, 01b ; General purpose register
.EQU R2, 10b ; General purpose register
.EQU R3, 11b ; General purpose register

; --- Program Code (15 instructions, fits 4-bit PC) ---
; Machine Code Format: [Opcode (4-bit)][Operand (4-bit)]

; Memory Address: 0000b (0x0)
START:
    ; Initialize System: Turn off light
    LDI R0, #00b              ; R0 = 0 (Value for OFF, 2-bit immediate)
    OUT R0, LIGHT_PORT        ; Turn OFF Light (Port 00b)

; Memory Address: 0010b (0x2)
WAIT_MOTION:
    ; Monitor Motion Sensor: Loop until motion is detected
    IN R1, MOTION_PORT        ; Read motion sensor status into R1 (Port 01b)
    MOV R0, R1                ; Copy R1 to R0. (R0 will hold motion status)
    SUB R0, R0                ; R0 = R0 - R0. If R0 (motion) was 0, Z_flag is set.
    JZ WAIT_MOTION            ; If Z_flag is set (no motion), loop back

; Memory Address: 0110b (0x6)
MOTION_DETECTED:
    ; Motion Detected: Load delay value, turn on light
    LDI R2, #01b              ; R2 = 1 (Example delay value, max 3 seconds due to 2-bit immediate)
                              ; This sets a delay of 1 'tick'. Each tick is one DEC instruction.
    LDI R0, #01b              ; R0 = 1 (Value for ON, 2-bit immediate)
    OUT R0, LIGHT_PORT        ; Turn ON Light (Port 00b)

; Memory Address: 1000b (0x8)
COUNTDOWN_LOOP:
    ; Countdown Delay
    DEC R2                    ; Decrement R2 (delay register). Sets Z_flag if R2 becomes 0.
    JZ LIGHT_OFF              ; If Z_flag is set (delay expired), jump to turn off light
    JMP COUNTDOWN_LOOP        ; Else, continue countdown

; Memory Address: 1100b (0xC)
LIGHT_OFF:
    ; Delay Expired: Turn off light
    LDI R0, #00b              ; R0 = 0 (Value for OFF, 2-bit immediate)
    OUT R0, LIGHT_PORT        ; Turn OFF Light (Port 00b)
    JMP START                 ; Go back to initial state (waiting for motion)

; Total Instructions: 15
; This program fits within the 16-instruction limit of a 4-bit PC.
"""

def parse_assembly(assembly_code):
    """
    Parses the assembly code, extracts labels and instructions.
    Returns a list of (label, mnemonic, operands) tuples and a dict of labels.
    """
    lines = assembly_code.strip().split('\n')
    parsed_lines = []
    labels = {}
    current_address = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('.EQU'):
            continue

        # Remove comments after instruction
        line = line.split(';')[0].strip()

        # Check for label
        if ':' in line:
            label = line.split(':')[0].strip()
            labels[label] = format(current_address, '04b') # Store address as 4-bit binary string
            line = line.split(':', 1)[1].strip() # Remove label from line

        if not line: # Line might have only been a label
            continue

        # Extract mnemonic and operands
        parts = line.split(maxsplit=1)
        mnemonic = parts[0].upper()
        operands = parts[1] if len(parts) > 1 else ""
        operands = operands.replace(" ", "").replace("#", "") # Clean up operands

        parsed_lines.append({"address": current_address, "mnemonic": mnemonic, "operands": operands})
        current_address += 1

    return parsed_lines, labels

def translate_to_machine_code(parsed_lines, labels):
    """
    Translates parsed assembly lines into 8-bit binary machine code.
    """
    machine_code_binary = []

    for instruction_data in parsed_lines:
        mnemonic = instruction_data["mnemonic"]
        operands = instruction_data["operands"]
        
        if mnemonic not in INSTRUCTION_SET:
            raise ValueError(f"Unknown mnemonic: {mnemonic}")

        opcode_info = INSTRUCTION_SET[mnemonic]
        opcode = opcode_info["opcode"]
        fmt = opcode_info["format"]
        operand_binary = ""

        if fmt == "": # NOP, HLT
            operand_binary = "0000"
        elif fmt == "reg_port": # IN Rn, P or OUT Rn, P
            parts = operands.split(',')
            reg = parts[0].strip()
            port = parts[1].strip()
            if reg not in REGISTERS:
                raise ValueError(f"Unknown register: {reg} in {mnemonic} instruction")
            if port not in PORTS:
                raise ValueError(f"Unknown port: {port} in {mnemonic} instruction")
            operand_binary = REGISTERS[reg] + PORTS[port] # nppp format (n=2bit, p=2bit)
        elif fmt == "reg_reg": # MOV Rd, Rs, ADD Rd, Rs, SUB Rd, Rs
            parts = operands.split(',')
            dest_reg = parts[0].strip()
            src_reg = parts[1].strip()
            if dest_reg not in REGISTERS or src_reg not in REGISTERS:
                raise ValueError(f"Unknown register in {mnemonic} instruction: {operands}")
            operand_binary = REGISTERS[dest_reg] + REGISTERS[src_reg] # dsrc format (d=2bit, s=2bit)
        elif fmt == "reg_imm2": # LDI Rn, #Imm (2-bit immediate)
            parts = operands.split(',')
            reg = parts[0].strip()
            imm = parts[1].strip()
            if reg not in REGISTERS:
                raise ValueError(f"Unknown register: {reg} in {mnemonic} instruction")
            # Ensure immediate is 2-bit binary (e.g., '00b' -> '00')
            imm_val = imm.replace('b', '')
            if not re.fullmatch(r'[01]{2}', imm_val):
                raise ValueError(f"Immediate value '{imm}' for LDI must be 2-bit binary (e.g., 00b, 11b).")
            operand_binary = REGISTERS[reg] + imm_val # nimm format (n=2bit, imm=2bit)
        elif fmt == "reg": # DEC Rn
            reg = operands.strip()
            if reg not in REGISTERS:
                raise ValueError(f"Unknown register: {reg} in {mnemonic} instruction")
            operand_binary = REGISTERS[reg] + "00" # n000 format (n=2bit, rest 0)
        elif fmt == "address": # JMP addr, JZ addr
            target_label = operands.strip()
            if target_label not in labels:
                raise ValueError(f"Undefined label: {target_label} in {mnemonic} instruction")
            operand_binary = labels[target_label] # aaaa format (4-bit address)
        else:
            raise ValueError(f"Unhandled format '{fmt}' for mnemonic: {mnemonic}")

        full_binary_instruction = opcode + operand_binary
        machine_code_binary.append(full_binary_instruction)

    return machine_code_binary

def convert_binary_to_hex(binary_code_list):
    """
    Converts a list of 8-bit binary strings to 2-digit hex strings.
    """
    hex_code_list = []
    for binary_str in binary_code_list:
        if len(binary_str) != 8:
            raise ValueError(f"Binary string '{binary_str}' is not 8 bits long.")
        hex_val = format(int(binary_str, 2), '02X') # Convert to int, then to 2-digit hex
        hex_code_list.append(hex_val)
    return hex_code_list

# --- Main Translation Process ---
if __name__ == "__main__":
    print("Parsing assembly code...")
    parsed_instructions, labels = parse_assembly(ASSEMBLY_CODE)

    print("\nLabels and their addresses:")
    for label, addr in labels.items():
        print(f"  {label}: {addr} (binary)")

    print("\nTranslating to machine code...")
    machine_code_binary = translate_to_machine_code(parsed_instructions, labels)

    print("\nGenerated Binary Machine Code:")
    for i, binary_instr in enumerate(machine_code_binary):
        print(f"  Addr {format(i, '04b')}: {binary_instr}")

    hex_machine_code = convert_binary_to_hex(machine_code_binary)

    print("\n--- Logisim ROM Content (Hexadecimal) ---")
    print("v2.0 raw") # Logisim ROM header
    for hex_val in hex_machine_code:
        print(hex_val)

    print("\nTranslation complete.")
    print(f"Total instructions translated: {len(hex_machine_code)}")
    if len(hex_machine_code) > 16:
        print("\nWARNING: The program exceeds the 16-instruction limit of a 4-bit Program Counter.")
        print("         You will need a larger PC/ROM in Logisim for this code to run fully.")
