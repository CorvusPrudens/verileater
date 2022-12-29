
let a = 8
let b = 5
let quotient = 0

divide:
    lda a
    sub b
    sta a
    out
    jc done
    lda quotient
    adi 1
    sta quotient
    j divide

done:
    add b
    out
    hlt
