from engine.strategies import ma_strategy, momentum, breakout

def vote(df):

    signals = [
        ma_strategy(df),
        momentum(df),
        breakout(df)
    ]

    score = {"BUY":0,"SELL":0,"HOLD":0}

    for s in signals:
        score[s] += 1

    return max(score, key=score.get)
