import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
daemon = False
max_requests = 1000
user = "advocate"
group = "advocate"
proctitle = "advocate_example"
