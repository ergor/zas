
main:
    ldi 0xF5, r0
    ldi 0x01, r1
    jmp $loop

    shr r1          # fillers, should be skipped by the JMP
    shr r1

loop:
    add r1
    jmpnz $loop     # add 1 to r0 until running over

    ldi 0x01, r0    # reset r0 to 1
loop2:
    shl r1          # r1 should be 1; shift left by 1
    or  r1          # and set lowest bit in r0
    jmpns $loop2    # until all bits are set
