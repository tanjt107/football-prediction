function factorial(n) {
    if (n === 0) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}

if (projScore1 === null || projScore2 === null || handicap === null) {
    return [null, null, null];
}

let handicaps = String(handicap).split('/').map(function(x) {
    return parseFloat(x);
});

let prob1 = new Array(goalDiff + 1).fill(0);
let prob2 = new Array(goalDiff + 1).fill(0);

for (let i = 0; i < goalDiff; i++) {
    prob1[i] = Math.exp(-projScore1) * Math.pow(projScore1, i) / factorial(i);
    prob2[i] = Math.exp(-projScore2) * Math.pow(projScore2, i) / factorial(i);
}

prob1[goalDiff] = 1 - prob1.reduce(function(a, b) {
    return a + b;
}, 0);
prob2[goalDiff] = 1 - prob2.reduce(function(a, b) {
    return a + b;
}, 0);

let probWin1 = 0;
let probDraw = 0;
let probWin2 = 0;

for (let h of handicaps) {
    for (let i = 0; i <= goalDiff; i++) {
        for (let j = 0; j <= goalDiff; j++) {
            let totalScore1 = i + h;
            if (totalScore1 > j) {
                probWin1 += prob1[i] * prob2[j];
            } else if (totalScore1 < j) {
                probWin2 += prob1[i] * prob2[j];
            } else {
                probDraw += prob1[i] * prob2[j];
            }
        }
    }
}

let handicapCount = handicaps.length;
probWin1 = probWin1 / handicapCount;
probDraw = probDraw / handicapCount;
probWin2 = probWin2 / handicapCount;

return [probWin1, probDraw, probWin2];