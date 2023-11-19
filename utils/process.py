from concurrent.futures import ThreadPoolExecutor


def thread_pool_results(function, args_arr):
    with ThreadPoolExecutor() as executor:
        return list(map(lambda args: executor.submit(function, args), args_arr))


def get_future_errors(results):
    return list(map(lambda future: str(future.exception()), filter(lambda future: future.exception(), results)))
