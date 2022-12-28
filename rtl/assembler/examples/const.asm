let variable = 0
const INCREMENT = 1

up:
    out
    lda variable
    adi INCREMENT
    sta variable
    jc down
    j up

down:
    out
    lda variable
    sbi INCREMENT
    sta variable
    jz up
    j down
