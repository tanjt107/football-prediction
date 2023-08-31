function factorial(n) {
    if (n === 0) {
        return 1;
    }
    return n * factorial(n - 1);
}

let prob1 = Array(goalDiff + 1);
let prob2 = Array(goalDiff + 1);

for (let i = 0; i < goalDiff; i++) {
    prob1[i] = Math.exp(-projScore1) * Math.pow(projScore1, i) / factorial(i);
    prob2[i] = Math.exp(-projScore2) * Math.pow(projScore2, i) / factorial(i);
}
prob1[goalDiff] = 1 - prob1.reduce((a, b) => a + b, 0);
prob2[goalDiff] = 1 - prob2.reduce((a, b) => a + b, 0);

let probWin1 = 0;
let probDraw = 0;
let probWin2 = 0;

for (let i = 0; i <= goalDiff; i++) {
    for (let j = 0; j <= goalDiff; j++) {
        if (i > j) {
            probWin1 += prob1[i] * prob2[j]
        } else if (i < j) {
            probWin2 += prob1[i] * prob2[j]
        } else {
            probDraw += prob1[i] * prob2[j]
        }
    }
}
return [probWin1, probDraw, probWin2]