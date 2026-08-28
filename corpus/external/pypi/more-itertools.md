---
date: 2026-05-22T14:14:28+0000
source: https://pypi.org/project/more-itertools/
---
[image: https://readthedocs.org/projects/more-itertools/badge/?version=latest]

Python’s itertools library is a gem - you can compose elegant solutions
for a variety of problems with the functions it provides. In more-itertools
we collect additional building blocks, recipes, and routines for working with
Python iterables.

| Grouping | chunked,
ichunked,
chunked_even,
sliced,
constrained_batches,
distribute,
divide,
split_at,
split_before,
split_after,
split_into,
split_when,
bucket,
unzip,
batched,
grouper,
partition |
| Lookahead and lookback | spy,
peekable,
seekable |
| Windowing | windowed,
substrings,
substrings_indexes,
stagger,
windowed_complete,
pairwise,
triplewise,
sliding_window,
subslices |
| Augmenting | count_cycle,
intersperse,
padded,
repeat_each,
mark_ends,
repeat_last,
adjacent,
groupby_transform,
pad_none,
ncycles |
| Combining | collapse,
sort_together,
interleave,
interleave_longest,
interleave_evenly,
interleave_randomly,
zip_offset,
zip_broadcast,
flatten,
roundrobin,
prepend,
value_chain,
partial_product |
| Concurrency | concurrent_tee,
serialize,
synchronized |
| Summarizing | ilen,
unique_to_each,
sample,
consecutive_groups,
run_length,
map_reduce,
join_mappings,
exactly_n,
is_sorted,
all_equal,
all_unique,
argmin,
argmax,
minmax,
first_true,
quantify,
iequals |
| Selecting | islice_extended,
first,
last,
one,
only,
strictly_n,
strip,
lstrip,
rstrip,
filter_except,
map_except,
filter_map,
iter_suppress,
nth_or_last,
extract,
unique_in_window,
before_and_after,
nth,
take,
tail,
unique_everseen,
unique_justseen,
unique,
duplicates_everseen,
duplicates_justseen,
classify_unique,
longest_common_prefix,
takewhile_inclusive |
| Math | dft,
idft,
convolve,
dotproduct,
matmul,
polynomial_from_roots,
polynomial_derivative,
polynomial_eval,
reshape,
sum_of_squares,
transpose |
| Integer math | factor,
is_prime,
multinomial,
nth_prime,
sieve,
totient |
| Statistics | running_min,
running_max,
running_mean,
running_median,
running_statistics |
| Combinatorics | circular_shifts,
derangements,
gray_product,
outer_product,
partitions,
set_partitions,
powerset,
powerset_of_sets |
| distinct_combinations,
distinct_permutations |
| combination_index,
combination_with_replacement_index,
permutation_index,
product_index |
| nth_combination,
nth_combination_with_replacement,
nth_permutation,
nth_product |
| random_combination,
random_combination_with_replacement,
random_derangement,
random_permutation,
random_product |
| Wrapping | always_iterable,
always_reversible,
countable,
consumer,
iter_except,
sized_iterator with_iter |
| Others | locate,
rlocate,
replace,
numeric_range,
side_effect,
iterate,
loops,
difference,
make_decorator,
SequenceView,
time_limited,
map_if,
iter_index,
consume,
tabulate,
repeatfunc,
doublestarmap |

## Getting started

To get started, install the library with pip:

```
pip install more-itertools
```

The recipes from the itertools docs
are included in the top-level package:

```
>>> from more_itertools import flatten
>>> iterable = [(0, 1), (2, 3)]
>>> list(flatten(iterable))
[0, 1, 2, 3]
```

Several new recipes are available as well:

```
>>> from more_itertools import chunked
>>> iterable = [0, 1, 2, 3, 4, 5, 6, 7, 8]
>>> list(chunked(iterable, 3))
[[0, 1, 2], [3, 4, 5], [6, 7, 8]]

>>> from more_itertools import spy
>>> iterable = (x * x for x in range(1, 6))
>>> head, iterable = spy(iterable, n=3)
>>> list(head)
[1, 4, 9]
>>> list(iterable)
[1, 4, 9, 16, 25]
```

For the full listing of functions, see the API documentation.

## Links elsewhere

Blog posts about more-itertools:

- Yo, I heard you like decorators
- Tour of Python Itertools (Alternate)
- Real-World Python More Itertools

## Development

more-itertools is maintained by @erikrose
and @bbayles, with help from many others.
If you have a problem or suggestion, please file a bug or pull request in this
repository. Thanks for contributing!

## Version History

The version history can be found in documentation.
