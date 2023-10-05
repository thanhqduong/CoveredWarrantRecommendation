import math
from scipy.stats import norm

def black_scholes_call_option(S, X, T, r, sigma):
    d1 = (math.log(S / X) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    N_d1 = norm.cdf(d1)
    N_d2 = norm.cdf(d2)
    
    call_price = S * N_d1 - X * math.exp(-r * T) * N_d2
    return call_price

def minimize_function(C, S, X, T, r, sigma, ratio):
    return C * ratio - black_scholes_call_option(S, X, T, r, sigma)

def derivative_function(C, S, X, T, r, sigma, ratio):
    y1 = minimize_function(C, S, X, T, r, sigma - 0.000025, ratio)
    y2 = minimize_function(C, S, X, T, r, sigma + 0.000025, ratio)
    return (y2-y1) / 0.00005

def newtonRaphson(C, S, X, T, r, sigma, ratio):
    count = 10000
    e = 0.25
    x = sigma
    condition = True
    while condition:
        count -= 1
        if derivative_function(C, S, X, T, r, x, ratio) != 0:
            x -=  minimize_function(C, S, X, T, r, x, ratio)/derivative_function(C, S, X, T, r, x, ratio)
            condition = (abs(minimize_function(C, S, X, T, r, x, ratio)) <= e) and (count > 0)
        else:
            condition = False
            print('divided by 0')
    return x

def find_volatility(C, S, X, T, ratio):
    start_volatility = [ 0.3, 0.4, 0.5] # avoid local min/max
    r = 0.02
    volatility = []
    abs_check = []
    for start_sigma in start_volatility:
        volatility.append( newtonRaphson(C, S, X, T, r, start_sigma, ratio) )
        abs_check.append( abs(minimize_function(C, S, X, T, r, volatility[-1], ratio)) )
    min_val = min(abs_check)
    idx = abs_check.index(min_val)
    return volatility[idx]