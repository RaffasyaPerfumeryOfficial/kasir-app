def bulat_harga(x):
    if x <= 2000:
        return 2000
    if x <= 2699:
        return 2500
    if x <= 2999:
        return 3000
    if x <= 3499:
        return 3500
    if x <= 3999:
        return 4000
    if x <= 4999:
        return 5000
    if x <= 5999:
        return 6000
    if x <= 6999:
        return 6500
    if x <= 8000:
        return 7500
    if x <= 10000:
        return 9000
    return int(round(x / 1000.0) * 1000)
