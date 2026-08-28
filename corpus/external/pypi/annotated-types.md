# annotated-types

[image: CI] [image: pypi] [image: versions] [image: license]

PEP-593 added typing.Annotated as a way of
adding context-specific metadata to existing types, and specifies that
Annotated[T, x] should be treated as T by any tool or library without special
logic for x.

This package provides metadata objects which can be used to represent common
constraints such as upper and lower bounds on scalar values and collection sizes,
a Predicate marker for runtime checks, and
descriptions of how we intend these metadata to be interpreted. In some cases,
we also note alternative representations which do not require this package.

## Install

```
pip install annotated-types
```

## Examples

```
from typing import Annotated
from annotated_types import Gt, Len, Predicate

class MyClass:
    age: Annotated[int, Gt(18)]                         # Valid: 19, 20, ...
                                                        # Invalid: 17, 18, "19", 19.0, ...
    factors: list[Annotated[int, Predicate(is_prime)]]  # Valid: 2, 3, 5, 7, 11, ...
                                                        # Invalid: 4, 8, -2, 5.0, "prime", ...

    my_list: Annotated[list[int], Len(0, 10)]           # Valid: [], [10, 20, 30, 40, 50]
                                                        # Invalid: (1, 2), ["abc"], [0] * 20
```

## Documentation

While annotated-types avoids runtime checks for performance, users should not
construct invalid combinations such as MultipleOf("non-numeric") or Annotated[int, Len(3)].
Downstream implementors may choose to raise an error, emit a warning, silently ignore
a metadata item, etc., if the metadata objects described below are used with an
incompatible type - or for any other reason!

### Gt, Ge, Lt, Le

Express inclusive and/or exclusive bounds on orderable values - which may be numbers,
dates, times, strings, sets, etc. Note that the boundary value need not be of the
same type that was annotated, so long as they can be compared: Annotated[int, Gt(1.5)]
is fine, for example, and implies that the value is an integer x such that x > 1.5.

We suggest that implementors may also interpret functools.partial(operator.le, 1.5)
as being equivalent to Gt(1.5), for users who wish to avoid a runtime dependency on
the annotated-types package.

To be explicit, these types have the following meanings:

- Gt(x) - value must be "Greater Than" x - equivalent to exclusive minimum
- Ge(x) - value must be "Greater than or Equal" to x - equivalent to inclusive minimum
- Lt(x) - value must be "Less Than" x - equivalent to exclusive maximum
- Le(x) - value must be "Less than or Equal" to x - equivalent to inclusive maximum

### Interval

Interval(gt, ge, lt, le) allows you to specify an upper and lower bound with a single
metadata object. None attributes should be ignored, and non-None attributes
treated as per the single bounds above.

### MultipleOf

MultipleOf(multiple_of=x) might be interpreted in two ways:

1. Python semantics, implying value % multiple_of == 0, or
1. JSONschema semantics,
where int(value / multiple_of) == value / multiple_of.

We encourage users to be aware of these two common interpretations and their
distinct behaviours, especially since very large or non-integer numbers make
it easy to cause silent data corruption due to floating-point imprecision.

We encourage libraries to carefully document which interpretation they implement.

### MinLen, MaxLen, Len

Len() implies that min_length <= len(value) <= max_length - lower and upper bounds are inclusive.

As well as Len() which can optionally include upper and lower bounds, we also
provide MinLen(x) and MaxLen(y) which are equivalent to Len(min_length=x)
and Len(max_length=y) respectively.

Len, MinLen, and MaxLen may be used with any type which supports len(value).

Examples of usage:

- Annotated[list, MaxLen(10)] (or Annotated[list, Len(max_length=10)]) - list must have a length of 10 or less
- Annotated[str, MaxLen(10)] - string must have a length of 10 or less
- Annotated[list, MinLen(3)] (or Annotated[list, Len(min_length=3)]) - list must have a length of 3 or more
- Annotated[list, Len(4, 6)] - list must have a length of 4, 5, or 6
- Annotated[list, Len(8, 8)] - list must have a length of exactly 8

#### Changed in v0.4.0

- min_inclusive has been renamed to min_length, no change in meaning
- max_exclusive has been renamed to max_length, upper bound is now inclusive instead of exclusive
- The recommendation that slices are interpreted as Len has been removed due to ambiguity and different semantic
meaning of the upper bound in slices vs. Len

See issue #23 for discussion.

### Timezone

Timezone can be used with a datetime or a time to express which timezones
are allowed. Annotated[datetime, Timezone(None)] must be a naive datetime.
Timezone[...] (literal ellipsis)
expresses that any timezone-aware datetime is allowed. You may also pass a specific
timezone string or tzinfo
object such as Timezone(timezone.utc) or Timezone("Africa/Abidjan") to express that you only
allow a specific timezone, though we note that this is often a symptom of fragile design.

#### Changed in v0.x.x

- Timezone accepts tzinfo objects instead of
timezone, extending compatibility to zoneinfo and third party libraries.

### Unit

Unit(unit: str) expresses that the annotated numeric value is the magnitude of
a quantity with the specified unit. For example, Annotated[float, Unit("m/s")]
would be a float representing a velocity in meters per second.

Please note that annotated_types itself makes no attempt to parse or validate
the unit string in any way. That is left entirely to downstream libraries,
such as pint or
astropy.units.

An example of how a library might use this metadata:

```
from annotated_types import Unit
from typing import Annotated, TypeVar, Callable, Any, get_origin, get_args

# given a type annotated with a unit:
Meters = Annotated[float, Unit("m")]

# you can cast the annotation to a specific unit type with any
# callable that accepts a string and returns the desired type
T = TypeVar("T")
def cast_unit(tp: Any, unit_cls: Callable[[str], T]) -> T | None:
    if get_origin(tp) is Annotated:
        for arg in get_args(tp):
            if isinstance(arg, Unit):
                return unit_cls(arg.unit)
    return None

# using `pint`
import pint
pint_unit = cast_unit(Meters, pint.Unit)

# using `astropy.units`
import astropy.units as u
astropy_unit = cast_unit(Meters, u.Unit)
```

### Predicate

Predicate(func: Callable) expresses that func(value) is truthy for valid values.
Users should prefer the statically inspectable metadata above, but if you need
the full power and flexibility of arbitrary runtime predicates... here it is.

For some common constraints, we provide generic types:

- LowerCase = Annotated[T, Predicate(str.islower)]
- UpperCase = Annotated[T, Predicate(str.isupper)]
- IsDigit = Annotated[T, Predicate(str.isdigit)]
- IsFinite = Annotated[T, Predicate(math.isfinite)]
- IsNotFinite = Annotated[T, Predicate(Not(math.isfinite))]
- IsNan = Annotated[T, Predicate(math.isnan)]
- IsNotNan = Annotated[T, Predicate(Not(math.isnan))]
- IsInfinite = Annotated[T, Predicate(math.isinf)]
- IsNotInfinite = Annotated[T, Predicate(Not(math.isinf))]

so that you can write e.g. x: IsFinite[float] = 2.0 instead of the longer
(but exactly equivalent) x: Annotated[float, Predicate(math.isfinite)] = 2.0.

Some libraries might have special logic to handle known or understandable predicates,
for example by checking for str.isdigit and using its presence to both call custom
logic to enforce digit-only strings, and customise some generated external schema.
Users are therefore encouraged to avoid indirection like lambda s: s.lower(), in
favor of introspectable methods such as str.lower or re.compile("pattern").search.

To enable basic negation of commonly used predicates like math.isnan without introducing introspection that makes it impossible for implementers to introspect the predicate we provide a Not wrapper that simply negates the predicate in an introspectable manner. Several of the predicates listed above are created in this manner.

We do not specify what behaviour should be expected for predicates that raise
an exception. For example Annotated[int, Predicate(str.isdigit)] might silently
skip invalid constraints, or statically raise an error; or it might try calling it
and then propagate or discard the resulting
TypeError: descriptor 'isdigit' for 'str' objects doesn't apply to a 'int' object
exception. We encourage libraries to document the behaviour they choose.

### Doc

doc() can be used to add documentation information in Annotated, for function and method parameters, variables, class attributes, return types, and any place where Annotated can be used.

It expects a value that can be statically analyzed, as the main use case is for static analysis, editors, documentation generators, and similar tools.

It returns a DocInfo class with a single attribute documentation containing the value passed to doc().

This is the early adopter's alternative form of the typing-doc proposal.

### Integrating downstream types with GroupedMetadata

Implementers may choose to provide a convenience wrapper that groups multiple pieces of metadata.
This can help reduce verbosity and cognitive overhead for users.
For example, an implementer like Pydantic might provide a Field or Meta type that accepts keyword arguments and transforms these into low-level metadata:

```
from dataclasses import dataclass
from typing import Iterator
from annotated_types import GroupedMetadata, Ge

@dataclass
class Field(GroupedMetadata):
    ge: int | None = None
    description: str | None = None

    def __iter__(self) -> Iterator[object]:
        # Iterating over a GroupedMetadata object should yield annotated-types
        # constraint metadata objects which describe it as fully as possible,
        # and may include other unknown objects too.
        if self.ge is not None:
            yield Ge(self.ge)
        if self.description is not None:
            yield Description(self.description)
```

Libraries consuming annotated-types constraints should check for GroupedMetadata and unpack it by iterating over the object and treating the results as if they had been "unpacked" in the Annotated type. The same logic should be applied to the PEP 646 Unpack type, so that Annotated[T, Field(...)], Annotated[T, Unpack[Field(...)]] and Annotated[T, *Field(...)] are all treated consistently.

Libraries consuming annotated-types should also ignore any metadata they do not recongize that came from unpacking a GroupedMetadata, just like they ignore unrecognized metadata in Annotated itself.

Our own annotated_types.Interval class is a GroupedMetadata which unpacks itself into Gt, Lt, etc., so this is not an abstract concern. Similarly, annotated_types.Len is a GroupedMetadata which unpacks itself into MinLen (optionally) and MaxLen.

### Consuming metadata

We intend to not be prescriptive as to how the metadata and constraints are used, but as an example of how one might parse constraints from types annotations see our implementation in test_main.py.

It is up to the implementer to determine how this metadata is used.
You could use the metadata for runtime type checking, for generating schemas or to generate example data, amongst other use cases.

## Design & History

This package was designed at the PyCon 2022 sprints by the maintainers of Pydantic
and Hypothesis, with the goal of making it as easy as possible for end-users to
provide more informative annotations for use by runtime libraries.

It is deliberately minimal, and following PEP-593 allows considerable downstream
discretion in what (if anything!) they choose to support. Nonetheless, we expect
that staying simple and covering only the most common use-cases will give users
and maintainers the best experience we can. If you'd like more constraints for your
types - follow our lead, by defining them and documenting them downstream!

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

annotated_types-0.8.0.tar.gz
 (15.9 kB
 view details)

Uploaded
 Jul 23, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

annotated_types-0.8.0-py3-none-any.whl
 (13.4 kB
 view details)

Uploaded
 Jul 23, 2026
 Python 3

## File details

Details for the file annotated_types-0.8.0.tar.gz.

### File metadata

- Download URL: annotated_types-0.8.0.tar.gz
- Upload date:
 Jul 23, 2026
- Size: 15.9 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.10.20

### File hashes

Hashes for annotated_types-0.8.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 13b2beaad985e05e2d6407ee4c4f35590b11f8d693a258a561055cac8f64cab7 | |
| MD5 | e82458911a4050ecf61f2a4c6015b7e9 | |
| BLAKE2b-256 | 5f56a8120250d128bed162cd73c76d45f6ef9991f3e068f62a8ee060afa3104a | |

See more details on using hashes here.

## File details

Details for the file annotated_types-0.8.0-py3-none-any.whl.

### File metadata

- Download URL: annotated_types-0.8.0-py3-none-any.whl
- Upload date:
 Jul 23, 2026
- Size: 13.4 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.10.20

### File hashes

Hashes for annotated_types-0.8.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0 | |
| MD5 | 1959042ee69ece0a558a30aa700cfc59 | |
| BLAKE2b-256 | 99918acff4f5e50511b911bbccb72b8628a49c68ce14148cd9f6431094859a90 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

0.8.0 This release

Jul 23, 2026
 2 files

0.7.0

May 20, 2024
 2 files

0.6.0

Oct 6, 2023
 2 files

0.5.0

May 31, 2023
 2 files

0.4.0

Oct 12, 2022
 2 files

0.3.1

Sep 25, 2022
 2 files

0.3.0

Sep 25, 2022
 2 files

0.2.0

Jun 15, 2022
 2 files

0.1.0

May 2, 2022
 2 files