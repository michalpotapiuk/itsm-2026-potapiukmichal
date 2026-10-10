<!-- ai-generated: 80% - ChatGPT helped structure the explanation; the measurement values come from my own Lab 3 load test through Toxiproxy. -->

# Client-server latency gap

I measured the service through Toxiproxy with a downstream latency toxic configured with 100 ms latency and 10 ms jitter.

The client-side p99 was 0.2429 seconds, while the server-side p99 from the svcdesk request histogram was 0.1375 seconds. The resulting gap was therefore 0.1054 seconds.

The difference exists because the server histogram measures the time spent handling the request inside svcdesk, including the call to kb-index, but it does not include the artificial downstream delay added by Toxiproxy after svcdesk has produced the response. The client measures the complete end-to-end response time, so it also observes the additional network delay.

This demonstrates why client-measured and server-measured latency can differ even when both measurements are correct. From the user's perspective, the extra delay is real, while the application itself cannot see it in its internal request-duration histogram.