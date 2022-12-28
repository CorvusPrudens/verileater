
up:
    out
    adi 1
    jc down
    j up

down:
    out
    sbi 1
    jz up
    j down
