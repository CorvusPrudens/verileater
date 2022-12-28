let zero = 0
let one = 1
let previous = 1

reset:
    lda one
    sta previous
    lda zero

main_loop:
    out
    add previous
    sta previous
    jc reset
    j main_loop
