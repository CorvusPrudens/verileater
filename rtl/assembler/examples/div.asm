
let a = 20
let b = 2
let quotient = 0

divide:
    lda a
    sub b
    sta a
    jz done
    lda quotient
    adi 1
    sta quotient
    out
    j divide

done:
    lda quotient
    adi 1
    out
    hlt
