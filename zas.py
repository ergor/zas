
# syntax:
# OP
# OP reg
# OP reg, reg
# OP [addr], reg
# OP reg, [addr]
# OP value, reg
# OP reg, value

IMM_DATA = "DATA"
IMM_ADDR = "ADDR"

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


def eval_imm(imm):
    if imm[0] == "[" and imm[-1] == "]":
        return (my_int(imm[1:-1]), IMM_ADDR)
    return (my_int(imm), IMM_DATA)


def split_bytes(val):
    high = (val >> 8) & 0xFF
    low  =  val       & 0xFF
    return (high, low) # big endian order


## SAFE WRAPPERS ##
def safe_has_oprs(op, oprs):
    if oprs == []:
        print(op + ": operands required")
        exit(1)


def safe_get_oprs(op, oprs, n):
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


def safe_eval_imm(op, imm, typ):
    imm = eval_imm(imm)
    success, imm_val, imm_typ = imm[0][0], imm[0][1], imm[1]
    if not success:
        print(op + ": invalid number format")
        exit(1)
    if imm_typ != typ:
        print(op + ": unexpected immediate data type")
        exit(1)
    return imm_val


## PARSERS ##
def parse_reg2reg(op, oprs):
    safe_has_oprs(op, oprs)
    oprs = safe_get_oprs(op, oprs, 2)

    rs = safe_get_reg(op, oprs[0])
    rd = safe_get_reg(op, oprs[1])

    base_val, _ = ops[op]
    return ( base_val + src_reg(rs) + dst_reg(rd), )


def parse_ld(op, oprs):
    safe_has_oprs(op, oprs)
    oprs = safe_get_oprs(op, oprs, 2)

    imm = safe_eval_imm(op,oprs[0], IMM_ADDR)

    base_val, _ = ops[op]
    high, low = split_bytes(imm)
    rd = safe_get_reg(op, oprs[1])

    return ( base_val + dst_reg(rd), high, low )


def parse_ldi(op, oprs):
    safe_has_oprs(op, oprs)
    oprs = safe_get_oprs(op, oprs, 2)

    imm = safe_eval_imm(op, oprs[0], IMM_DATA)

    imm &= 0xFF
    base_val, _ = ops[op]
    rd = safe_get_reg(op, oprs[1])

    return ( base_val + dst_reg(rd), imm )


def parse_single_reg(reg_evaluator):
    def parse(op, oprs):
        safe_has_oprs(op, oprs)
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
    string.strip()
    strs = [s.upper() for s in string.split(None, 1)]    

    op = strs[0]
    oprs = [] if len(strs) == 1 else strs[1]

    _, parser = ops.get(op)
    if parser is not None:
        print(parser(op, oprs))
    else:
        print(op + ": no such instruction")
        exit(1)

ops = {
    # "name" : (base_value, parser_func)
    "NOP" : (0o000, parse_no_oprs),
    "POP" : (0o040, parse_single_reg(dst_reg)),
    "LDI" : (0o050, parse_ldi),
    "LD"  : (0o060, parse_ld),
    "MOV" : (0o100, parse_reg2reg),
    "SUB" : (0o202, parse_single_reg(src_reg)),
    "ADD" : (0o203, parse_single_reg(src_reg)),
    "XOR" : (0o204, parse_single_reg(src_reg)),
    "OR"  : (0o205, parse_single_reg(src_reg)),
    "AND" : (0o206, parse_single_reg(src_reg)),
    "PUSH": (0o300, parse_single_reg(src_reg)),
    "SBB" : (0o302, parse_single_reg(src_reg)),
    "ADC" : (0o303, parse_single_reg(src_reg)),
    "SHL" : (0o304, parse_single_reg(src_reg)),
    "SHR" : (0o305, parse_single_reg(src_reg)),
}


def main():
    while True:
        line = input()
        parse_ln(line)

main()
