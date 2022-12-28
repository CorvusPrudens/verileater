let a = 2
let b = 4

// Basic loop
start:
    lda a
    add b
    sta a
    out
    j start
