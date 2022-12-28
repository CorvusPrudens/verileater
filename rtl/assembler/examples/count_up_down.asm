up:
    out
    adi 1
    jnc up

down:
    out
    sbi 1
    jnz down
