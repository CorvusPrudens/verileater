let n_minus_2
let n_minus_1
let n

reset:
    ldi 0
    sta n_minus_2
    ldi 1
    sta n_minus_1

main_loop:
    out
    add n_minus_2
    sta n
    lda n_minus_1
    sta n_minus_2
    lda n
    sta n_minus_1
    jc reset
    j main_loop
