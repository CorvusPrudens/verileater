let variable = 0
const INCREMENT = 1

up:
    out
    lda variable
    adi INCREMENT
    sta variable
    jnc up

down:
    out
    lda variable
    sbi INCREMENT
    sta variable
    jz up
    j down
