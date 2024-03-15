"""descriptions for utilities"""


def clamp(v: int, l: int, h: int) -> int:
    """return a value between 'l' and 'h'"""
    return max(l, min(v, h))


def bin_search(arr, target) -> (int, int):
    """binary search that returns (status, closest index)"""
    f = 0  # a factor that corrects closest index
    h = len(arr) - 1
    l = 0
    m = 0
    while l <= h:  # while pointers haven't passed one another
        m = (l + h) // 2
        if arr[m] < target:
            h = m - 1  # search space greater side
            f = 0
        elif arr[m] > target:
            l = m + 1  # search space smaller side
            f = 1
        elif arr[m] == target:
            return (1, m)
    return (0, m + f)
