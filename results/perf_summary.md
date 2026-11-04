# Task 7 measurements (standard load test, 2 replicas, results/loadtest_stats.csv)
- requests 302, failures 0, error rate 0.00 %
- p50 1600 ms, p95 1900 ms
- throughput 2.53 req/s
- CPU per Pod ~998m (at the 1-CPU limit), memory ~393-406 Mi (results/top_pods.txt)
- cold start median 10.5 s (results/cold_start.txt)

## Cost per 1,000 requests (rate card, INR)
1. per replica per hour = 1 vCPU x 3.50 + 1 GiB x 0.45 = 3.95
2. 2 replicas = 7.90 per hour
3. requests per hour = 2.5334 x 3600 = 9,120.1
4. cost per 1,000 = 7.90 / 9,120.1 x 1000 = INR 0.866

## SLO
99% of /parse requests return HTTP 200 within 30 s, window = one standard load-test run (2 min).
Error budget = 1% x 302 = 3 requests. Used: 0 (0% of budget).
