
let a = 12
let b = 5
let product = 0

multiply:
    lda product
    add a
    sta product
    out
    lda b
    sbi 1
    sta b
    jz done
    j multiply

done:
    hlt
