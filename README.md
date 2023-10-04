# Vietnam Covered Warrants (CW) day-trading strategy Recommendation

### Overview: Identify short-term market mispricing of Covered Warrant for day-trading

### Methodology:
##### 0. Get real-time data
##### 1. Filter Covered Warrant to ensure liquidity
* This is the most simple way I found (that worked how I wanted); there are of course many ways that are more accurate:
a. For all CWs, list their traded volume $l$
b. Calculate $b = max(min(\text{median(l)}, mean(l)/4), 1000)$
c. Filter out CWs that their traded volume is less than $b$
##### 2. Find implied volatility $\sigma$ of each CW
a. Utilize the Black-Scholes (BS) formula
* Get the current call price; assuming other parameters are available besides the risk-free rate
* Risk-free rate: Spoiler: We will use $\sigma$ to compare CWs with each other, therefore, when $\Delta t$ (time to maturity) is large, it doesn't matter. To avoid risk when $\Delta t \approx 0$, choose a relatively small risk-free rate; I arbitrarily choose $2$% annually.
* We can refer to the BS formula as: $C = bs(\sigma)$ as we assumed other variables are known.

b. Since we cannot directly reverse-engineer the BS formula (to $bs^{-1}$) to find the implied volatility from the current call price, we can find the implied volatility using the Newton-Raphson method to find the root of the function $f(\sigma) = C - bs(\sigma)$
* Arbitrarily I choose the stop condition to be $\Delta C <= 0.5 \text{ VND} \approx 2 \cdot 10^{-5} \text{ USD}$, number of iteration $ = 10000$
* Filter out CW that $|Est.C - C|$ is large
##### 3. Find z-score
For each CW x, find z-score($\sigma_{x}$) with respect to all implied volatilities of the CWs with the same underlying stocks
* Assumption: I will use z-score to compare CWs, with lower z-score implies being lower-priced. Therefore, I can only calculate the z-scores of CWs with the same underlying stocks.
##### 4. Recommendation
* Rank CW base on their z-score
* My recommendation CW: top 3 CWs with lowest z-score

### Strategy and next step
1. At time $X$ on trading days, run program to get $3$ CWs as recommendation
2. Buy those CWs with proportion $Y$
3. On the same day, after $\Delta$ time (at time $X + \Delta$), sell those CWs

* Next step: find $X, Y, \Delta$ for optimization

#### Acknowledgement:
For the implementaion of the code, I use CW real-time data from scraping the website https://24hmoney.vn/covered-warrant/
