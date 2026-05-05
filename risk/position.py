def position(balance, confidence=0.7):

    if confidence > 0.8:
        return balance * 0.5, 10

    if confidence > 0.6:
        return balance * 0.3, 5

    if confidence > 0.4:
        return balance * 0.2, 3

    return balance * 0.1, 2
