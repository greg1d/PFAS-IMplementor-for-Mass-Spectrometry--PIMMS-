import bisect
import time
import numpy as np

# Example sorted array
np.random.seed(42)  # For reproducibility
array = sorted(np.random.randint(1, 1600, size=6000))
k = 5


def meets_condition(a, b):
    # Example condition: absolute difference less than or equal to k
    return abs(a - b) <= k


# Naive pairwise comparison
def naive_comparison(array, k):
    print("Naive Pairwise Comparison Results:")
    start_time = time.time()
    results = []
    n = len(array)
    calculations = 0  # Counter for number of comparisons
    for i in range(n):
        for j in range(i + 1, n):
            calculations += 1
            if meets_condition(array[i], array[j]):
                results.append((array[i], array[j]))
    end_time = time.time()
    print(f"Calculations: {calculations}")
    print(f"Time Taken: {end_time - start_time:.6f} seconds\n")
    return results, calculations


# Optimized binary search approach
def binary_search_comparison(array, k):
    print("Binary Search Comparison Results:")
    start_time = time.time()
    results = []
    n = len(array)
    calculations = 0  # Counter for number of comparisons
    for i in range(n):
        lower_bound = array[i] - k
        upper_bound = array[i] + k

        # Find the bounds using binary search
        j_start = bisect.bisect_left(array, lower_bound, i + 1)
        j_end = bisect.bisect_right(array, upper_bound, i + 1)

        # Iterate over the range of potential matches
        for j in range(j_start, j_end):
            calculations += 1
            if meets_condition(array[i], array[j]):
                results.append((array[i], array[j]))
    end_time = time.time()
    print(f"Calculations: {calculations}")
    print(f"Time Taken: {end_time - start_time:.6f} seconds\n")
    return results, calculations


# Run both methods
naive_results, naive_calculations = naive_comparison(array, k)
binary_results, binary_calculations = binary_search_comparison(array, k)

# Check if results are the same
print("Are the results identical?")
print(naive_results == binary_results)

# Compare calculations
print("\nNumber of calculations:")
print(f"Naive approach: {naive_calculations}")
print(f"Binary search approach: {binary_calculations}")
