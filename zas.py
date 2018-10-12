
# syntax:
# OP
# OP reg
# OP reg, reg
# OP $addr, reg
# OP reg, $addr
# OP value, reg
# OP $addr
# label:
# .directive


pc = 0      # program counter
memory = [0] * 2**16
# where to write? memory[addr in label_refs]
# what value to write? addr in label_defs
label_refs = [
    # ("name" , addr)
]
label_defs = {
    # "name" : addr
}

IMM_DATA = "DATA"
IMM_ADDR = "ADDR"
IMM_LABL = "LABL"
COMMENT = "#"
LABEL = ":"
BABE = 0xBABE

regs = {
    "R0" : 0,
    "R1" : 1,
    "R2" : 2,
    "R3" : 3,
    "R4" : 4,
    "R5" : 5,
    "R6" : 6,
    "R7" : 7,
}


## CONVERTERS ##
def try_int(string, radix):
    try:
        i = int(string, radix)
        return (True, i)
    except:
        return (False, -1)


def my_int(string):
    prefix = string[0:2].upper()
    if prefix == "0X" or prefix == "0B":
        return try_int(string, 0) # auto determine radix
    if prefix[0] == "0":
        return try_int(string, 8)
    return try_int(string, 10)


## HELPER FUNCS ##
def dst_reg(reg):
    return reg
def src_reg(reg):
    return reg << 3


# having two syntaxes helps catching these mistakes:
# LD 100, r0   # error: should have used LDI
def eval_imm(imm):
    typ = IMM_DATA
    if imm[0] == "$":
        typ = IMM_ADDR
        imm = imm[1:]
    success, val = my_int(imm)
    if not success and typ == IMM_ADDR:
        typ = IMM_LABL
        label_refs.append((imm, pc))  # assume it's a label reference
    return (success, val, typ)


def split_bytes(val):
    high = (val >> 8) & 0xFF
    low  =  val       & 0xFF
    return (high, low) # big endian order


## SAFE WRAPPERS ##
def safe_get_oprs(op, oprs, n):
    if oprs == []:
        print(op + ": operands required")
        exit(1)

    oprs = [o.strip() for o in oprs.split(',')]
    if len(oprs) != n:
        print(op + ": expected " + n + " operands")
        exit(1)
    return oprs


def safe_get_reg(op, reg):
    reg = regs.get(reg)
    if reg is None:
        print(op + ": invalid register")
        exit(1)
    return reg


def safe_eval_imm(op, imm, typ, allow_lbl=True):
    success, imm_val, imm_typ = eval_imm(imm)
    if allow_lbl and imm_typ == IMM_LABL:
        return BABE
    if not success:
        print(op + ": invalid number format")
        exit(1)
    if imm_typ != typ:
        print(op + ": unexpected immediate data type")
        exit(1)
    return imm_val


## PARSERS ##
def parse_reg2reg(op, oprs):
    oprs = safe_get_oprs(op, oprs, 2)

    rs = safe_get_reg(op, oprs[0])
    rd = safe_get_reg(op, oprs[1])

    base_val, _ = ops[op]
    return ( base_val + src_reg(rs) + dst_reg(rd), )


def parse_ld_st(reg_evaluator):
    def parse(op, oprs):
        oprs = safe_get_oprs(op, oprs, 2)
        reg = oprs[0] if reg_evaluator == src_reg else oprs[1]
        imm = oprs[1] if reg_evaluator == src_reg else oprs[0]

        reg = safe_get_reg(op,  reg)
        imm = safe_eval_imm(op, imm, IMM_ADDR)

        base_val, _ = ops[op]
        high, low = split_bytes(imm)
        
        return ( base_val + reg_evaluator(reg), high, low )
    return parse


def parse_ldi(op, oprs):
    oprs = safe_get_oprs(op, oprs, 2)

    imm = safe_eval_imm(op, oprs[0], IMM_DATA)

    imm &= 0xFF
    base_val, _ = ops[op]
    rd = safe_get_reg(op, oprs[1])

    return ( base_val + dst_reg(rd), imm )


def parse_single_reg(reg_evaluator):
    def parse(op, oprs):
        reg = safe_get_reg(op, safe_get_oprs(op, oprs, 1)[0])
        base_val, _ = ops[op]
        return ( base_val + reg_evaluator(reg), )
    return parse


def parse_no_oprs(op, oprs):
    if oprs != []:
        print(op + ": unexpected operands")
        exit(1)
    base_val, _ = ops[op]
    return ( base_val, )


def parse_ln(string):
    global pc
    ln = string.strip().split(COMMENT, 1)[0]
    if not ln:
        return

    if LABEL in ln:
        ln = ln.split(LABEL, 1)
        lbl = ln[0].strip().upper()
        if len(lbl) < 1:
            print("label cannot be empty")
            exit(1)
        if lbl in label_defs.keys():
            print(lbl + " is not unique")
            exit(1)
        label_defs[lbl] = pc
        if not ln[1]:
            return # if it was only a label definition on this line
        ln = ln[1]

    strs = [s.upper() for s in ln.split(None, 1)]

    op = strs[0]
    oprs = [] if len(strs) == 1 else strs[1]

    entry = ops.get(op)
    if entry is not None:
        _, parser = entry
        data = parser(op, oprs)
        #print(data)
        for i, byte in enumerate(data):
            memory[pc + i] = byte
            pc += 1
    else:
        print(op + ": no such instruction")
        exit(1)

ops = {
    # "name" : (base_value, parser_func)
    "NOP" : (0o000, parse_no_oprs),
    #"JMPS":(0o010, ),
    #"JMPZ":(0o011, ),
    #"JMPV":(0o012, ),
    #"JMPC":(0o013, ),
    #"JMPA":(0o014, ),
    #"CALL":(0o015, ),
    "RET" : (0o016, parse_no_oprs),
    #"JMP" :(0o017, ),
    #"JMPNS":(0o020, ),
    #"JMPNZ":(0o021, ),
    #"JMPNV":(0o022, ),
    #"JMPNC":(0o023, ),
    #"JMPNA":(0o024, ),
    "POP" : (0o040, parse_single_reg(dst_reg)),
    "LDI" : (0o050, parse_ldi),
    "LD"  : (0o060, parse_ld_st(dst_reg)),
    "IN"  : (0o070, parse_ld_st(dst_reg)),
    "MOV" : (0o100, parse_reg2reg),
    "ST"  : (0o200, parse_ld_st(src_reg)),
    "SUB" : (0o202, parse_single_reg(src_reg)),
    "ADD" : (0o203, parse_single_reg(src_reg)),
    "XOR" : (0o204, parse_single_reg(src_reg)),
    "OR"  : (0o205, parse_single_reg(src_reg)),
    "AND" : (0o206, parse_single_reg(src_reg)),
    "OUT" : (0o207, parse_ld_st(src_reg)),
    "PUSH": (0o300, parse_single_reg(src_reg)),
    "SBB" : (0o302, parse_single_reg(src_reg)),
    "ADC" : (0o303, parse_single_reg(src_reg)),
    "SHL" : (0o304, parse_single_reg(src_reg)),
    "SHR" : (0o305, parse_single_reg(src_reg)),
}


def main():
    while True:
        print(pc, end=" ")
        line = input()
        parse_ln(line)

main()
