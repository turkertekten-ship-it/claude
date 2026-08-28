# Pydantic Validation

[image: CI] [image: Coverage] [image: pypi] [image: CondaForge] [image: downloads] [image: versions] [image: license] [image: Pydantic v2] [image: llms.txt]

Data validation using Python type hints.

Fast and extensible, Pydantic plays nicely with your linters/IDE/brain.
Define how data should be in pure, canonical Python 3.9+; validate it with Pydantic.

## Pydantic Logfire :fire:

We've launched Pydantic Logfire to help you monitor your applications.
Learn more

## Pydantic V1.10 vs. V2

Pydantic V2 is a ground-up rewrite that offers many new features, performance improvements, and some breaking changes compared to Pydantic V1.

If you're using Pydantic V1 you may want to look at the
pydantic V1.10 Documentation or,
1.10.X-fixes git branch. Pydantic V2 also ships with the latest version of Pydantic V1 built in so that you can incrementally upgrade your code base and projects: from pydantic import v1 as pydantic_v1.

## Help

See documentation for more details.

## Installation

Install using pip install -U pydantic or conda install pydantic -c conda-forge.
For more installation options to make Pydantic even faster,
see the Install section in the documentation.

## A Simple Example

```
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: list[int] = []

external_data = {'id': '123', 'signup_ts': '2017-06-01 12:22', 'friends': [1, '2', b'3']}
user = User(**external_data)
print(user)
#> User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]
print(user.id)
#> 123
```

## Contributing

For guidance on setting up a development environment and how to make a
contribution to Pydantic, see
Contributing to Pydantic.

## Reporting a Security Vulnerability

See our security policy.

## Changelog

## v2.13.4 (2026-05-06)

GitHub release

### What's Changed

#### Packaging

- Bump libc from 0.2.155 to 0.2.185 by @Viicos in #13109
- Adapt pydantic-core linker flags on macOS by @washingtoneg and @Viicos in #13147

#### Fixes

- Preserve RootModel core metadata by @Viicos in #13129

## v2.13.3 (2026-04-20)

GitHub release

### What's Changed

#### Fixes

- Handle AttributeError subclasses with from_attributes by @Viicos in #13096

## v2.13.2 (2026-04-17)

GitHub release

### What's Changed

#### Fixes

- Fix ValidationInfo.field_name missing with model_validate_json() by @Viicos in #13084

## v2.13.1 (2026-04-15)

GitHub release

### What's Changed

#### Fixes

- Fix ValidationInfo.data missing with model_validate_json() by @davidhewitt in #13079

## v2.13.0 (2026-04-13)

GitHub release

The highlights of the v2.13 release are available in the blog post.
Several minor changes (considered non-breaking changes according to our versioning policy)
are also included in this release. Make sure to look into them before upgrading.

This release contains the updated pydantic.v1 namespace, matching version 1.10.26 which includes support for Python 3.14.

### What's Changed

See the beta releases for all changes sinces 2.12.

#### New Features

- Allow default factories of private attributes to take validated model data by @Viicos in #13013

#### Changes

- Warn when serializing fixed length tuples with too few items by @arvindsaripalli in #13016

#### Fixes

- Change type of Any when synthesizing _build_sources for BaseSettings.__init__() signature in the mypy plugin by @Viicos in #13049
- Fix model equality when using runtime extra configuration by @Viicos in #13062

#### Packaging

- Add zizmor for GitHub Actions workflow linting by @Viicos in #13039
- Update jiter to v0.14.0 to fix a segmentation fault on musl Linux by @Viicos in #13064

### New Contributors

- @arvindsaripalli made their first contribution in #13016

## v2.13.0b3 (2026-03-31)

GitHub release

### What's Changed

#### New Features

- Add ascii_only option to StringConstraints by @ai-man-codes in #12907
- Support exclude_if in computed fields by @andresliszt in #12748
- Push down constraints in unions involving MISSING sentinel by @Viicos in #12908

#### Changes

- Track extra fields set after init in model_fields_set by @navalprakhar in #12817
- Do not include annotations that are not part of named tuple fields by @galuszkak in #12951
- No longer fall back to trying all union members when the variant selected by discriminator fails to serialize by @navalprakhar in #12825

#### Fixes

- Support discriminator metadata outside union type alias by @Viicos in #12785
- Respect extras_schema when only extra_fields_behavior is set on the config in JSON Schema generation for typed dictionaries by @Viicos in #12810
- Ensure __pydantic_private__ is set in model_construct() with user-defined model_post_init() by @nightcityblade in #12816
- Handle all schema generation errors in InstanceOf by @Viicos in #12705
- Allow dynamic models created with create_model() to be used as annotations in the Mypy plugin by @Br1an67 in #12879
- Check for PlaceholderNode in Mypy plugin by @Viicos in #12929
- Try other branches in smart union in case of omit errors by @mikeedjones in #12758
- Patch unset attributes with MISSING during model serialization with exclude_unset by @davidhewitt in #12905
- Ensure custom __init__() is called when using model_validate_strings() by @siewcapital in #12897

#### Packaging

- Add riscv64 build target for manylinux by @boosterl in #12723

### New Contributors

- @kelsonbrito50 made their first contribution in #12860
- @boosterl made their first contribution in #12723
- @adityagiri3600 made their first contribution in #12868
- @navalprakhar made their first contribution in #12817
- @Br1an67 made their first contribution in #12879
- @rmorshea made their first contribution in #12910
- @N3XT3R1337 made their first contribution in #12922
- @ai-man-codes made their first contribution in #12907
- @Yume05-dev made their first contribution in #12953
- @galuszkak made their first contribution in #12951
- @siewcapital made their first contribution in #12897

## v2.13.0b2 (2026-02-24)

GitHub release

### What's Changed

#### Fixes

- Fix backported V1 namespace by @Viicos in #12855
- Allow any type form to be used in validate_as() by @bledden in #12846
- Fix walrus operator precedence in UrlConstraints.__get_pydantic_core_schema__() by @bysiber in #12826

### New Contributors

- @bledden made their first contribution in #12846
- @bysiber made their first contribution in #12827

## v2.13.0b1 (2026-02-23)

GitHub release

This is the first beta release of the 2.13 version, mainly providing bug fixes and performance improvements
for validation and serialization.

Notable changes include:

- Add a new polymorphic_serialization option, solving issues with serialize_as_any introduced in 2.12.
- Latest V1.10.26 release under the pydantic.v1 namespace. This version includes support for Python 3.14.
- The pydantic-core repository was merged inside the main pydantic one.

### What's Changed

#### New Features

- Add polymorphic_serialization option by @davidhewitt in #12518
- Support Root models with Literal root types as discriminator field types by @YassinNouh21 in #12680

#### Changes

- Migrate pydantic-core CI by @Viicos in #12752
- Import pydantic-core into pydantic by @davidhewitt in #12481
- Backport V1 changes up to v1.10.26 by @Viicos in #12663
- Use the complex() constructor unconditionally when validating complex Python data by @tanmaymunjal in #12498
- Add support for three-tuple input for Decimal by @tanmaymunjal in #12500
- Align @field_serializer logic with @field_validator by @Viicos in #12577
- Make PydanticUserError a RuntimeError instead of a TypeError by @poliakovva in #12579
- Remove redundant serialization attempts in nested unions by @davidhewitt in #12604
- Copy root value when making root model shallow copies by @YassinNouh21 in #12679
- Ensure deterministic JSON schema defaults by sorting sets by @drshvik in #12760

#### Performance

- Refactor DecoratorInfos.build() implementation by @Viicos in #12536
- Cache compiled regex in pydantic-core by @Viicos in #12549
- Optimize creation of Literal validators by @davidhewitt in #12569
- Optimize implementation of LookupKey by @davidhewitt in #12571
- Use python strings for field names by @davidhewitt in #12631
- Optimize datetime formatting code by @davidhewitt in #12626
- Validate JSON model data by iteration by @davidhewitt in #12550
- Optimize annotations evaluation of Pydantic models by @Viicos in #12681
- Optimize FieldInfo._copy() by @Viicos in #12727

#### Fixes

- Fix FieldInfo rebuilding when parameterizing generic models with an Annotated type by @Viicos in #12463
- Fix nested model schema deduplication in JSON schema generation by @marwan-alloreview in #12494
- Fix InitVar being ignored when using with the pydantic.Field() function by @Viicos in #12495
- Fix support for enums with NamedTuple as values by @Viicos in #12506
- Do not delete mock validator/serializer in rebuild_dataclass() by @Viicos in #12513
- Require test suite to pass with free threading, switch back to global generic types cache by @davidhewitt in #12537
- Refactor __pydantic_extra__ annotation handling by @Viicos in #12563
- Do not add claim of UUID "safety" provision by @davidhewitt in #12567
- Use Python hash to perform lookup in tagged union serializer by @davidhewitt in #12594
- Do not emit serialization warning MISSING sentinel is present in a nested model by @Viicos in #12635
- Do not eagerly evaluate annotations in signature logic by @Viicos in #12660
- Fix serialization of typed dict unions when exclude_none is set by @davidhewitt in #12677
- Do not reuse prebuilt serializers/validators on rebuilds by @lmmx in #12689
- Fix type annotation of field_definitions in create_model() by @lehmann-hqs in #12734
- Fix incorrect dataclass constructor signature when overriding class kw_only with Field() by @jfadia in #12741
- Use typing.Union when replacing types under Python 3.14 by @Viicos in #12733
- Improve ImportString error when internal imports fail by @tsembp in #12740
- Fix serializing complex numbers with negative zero imaginary part by @lhnwrk in #12770
- Preserve custom docstrings on stdlib dataclasses in JSON schema by @nightcityblade in #12815

#### Packaging

- Bump Rust url dependency from 2.5.4 to 2.5.7 in pydantic-core by @dependabot[bot] in #12508
- Bump Rust minimum version to 1.88, use edition 2024 by @davidhewitt and @Viicos in #12551 and #12752
- Bump PyO3 to 0.28, jiter to 0.13 by @davidhewitt in #12767

### New Contributors

- @marwan-alloreview made their first contribution in #12494
- @tanmaymunjal made their first contribution in #12498
- @poliakovva made their first contribution in #12579
- @lehmann-hqs made their first contribution in #12734
- @jfadia made their first contribution in #12741
- @tsembp made their first contribution in #12740
- @drshvik made their first contribution in #12760
- @lhnwrk made their first contribution in #12770
- @nightcityblade made their first contribution in #12815

## v2.12.5 (2025-11-26)

GitHub release

This is the fifth 2.12 patch release, addressing an issue with the MISSING sentinel and providing several documentation improvements.

The next 2.13 minor release will be published in a couple weeks, and will include a new polymorphic serialization feature addressing
the remaining unexpected changes to the serialize as any behavior.

- Fix pickle error when using model_construct() on a model with MISSING as a default value by @ornariece in #12522.
- Several updates to the documentation by @Viicos.

## v2.12.4 (2025-11-05)

GitHub release

This is the fourth 2.12 patch release, fixing more regressions, and reverting a change in the build() method
of the AnyUrl and Dsn types.

This patch release also fixes an issue with the serialization of IP address types, when serialize_as_any is used. The next patch release
will try to address the remaining issues with serialize as any behavior by introducing a new polymorphic serialization feature, that
should be used in most cases in place of serialize as any.

- Fix issue with forward references in parent TypedDict classes by @Viicos in #12427.

This issue is only relevant on Python 3.14 and greater.
- Exclude fields with exclude_if from JSON Schema required fields by @Viicos in #12430
- Revert URL percent-encoding of credentials in the build() method
of the AnyUrl and Dsn types by @davidhewitt in
pydantic-core#1833.

This was initially considered as a bugfix, but caused regressions and as such was fully reverted. The next release will include
an opt-in option to percent-encode components of the URL.
- Add type inference for IP address types by @davidhewitt in pydantic-core#1868.

The 2.12 changes to the serialize_as_any behavior made it so that IP address types could not properly serialize to JSON.
- Avoid getting default values from defaultdict by @davidhewitt in pydantic-core#1853.

This fixes a subtle regression in the validation behavior of the collections.defaultdict
type.
- Fix issue with field serializers on nested typed dictionaries by @davidhewitt in pydantic-core#1879.
- Add more pydantic-core builds for the three-threaded version of Python 3.14 by @davidhewitt in pydantic-core#1864.

## v2.12.3 (2025-10-17)

GitHub release

### What's Changed

This is the third 2.12 patch release, fixing issues related to the FieldInfo class, and reverting a change to the supported
after model validator function signatures.

- Raise a warning when an invalid after model validator function signature is raised by @Viicos in #12414.
Starting in 2.12.0, using class methods for after model validators raised an error, but the error wasn't raised concistently. We decided
to emit a deprecation warning instead.
- Add FieldInfo.asdict() method, improve documentation around FieldInfo by @Viicos in #12411.
This also add back support for mutations on FieldInfo classes, that are reused as Annotated metadata. However, note that this is still
not a supported pattern. Instead, please refer to the added example in the documentation.

The blog post section on changes was also updated to document the changes related to serialize_as_any.

## v2.12.2 (2025-10-14)

GitHub release

### What's Changed

#### Fixes

- Release a new pydantic-core version, as a corrupted CPython 3.10 manylinux2014_aarch64 wheel got uploaded (pydantic-core#1843).
- Fix issue with recursive generic models with a parent model class by @Viicos in #12398

## v2.12.1 (2025-10-13)

GitHub release

### What's Changed

This is the first 2.12 patch release, addressing most (but not all yet) regressions from the initial 2.12.0 release.

#### Fixes

- Do not evaluate annotations when inspecting validators and serializers by @Viicos in #12355
- Make sure None is converted as NoneType in Python 3.14 by @Viicos in #12370
- Backport V1 runtime warning when using Python 3.14 by @Viicos in #12367
- Fix error message for invalid validator signatures by @Viicos in #12366
- Populate field name in ValidationInfo for validation of default value by @Viicos in pydantic-core#1826
- Encode credentials in MultiHostUrl builder by @willswire in pydantic-core#1829
- Respect field serializers when using serialize_as_any serialization flag by @davidhewitt in pydantic-core#1829
- Fix various RootModel serialization issues by @davidhewitt in pydantic-core#1836

### New Contributors

- @willswire made their first contribution in pydantic-core#1829

## v2.12.0 (2025-10-07)

GitHub release

This is the final 2.12 release. It features the work of 20 external contributors and provides useful new features, along with initial Python 3.14 support.
Several minor changes (considered non-breaking changes according to our versioning policy)
are also included in this release. Make sure to look into them before upgrading.

Note that Pydantic V1 is not compatible with Python 3.14 and greater.

### What's Changed

See the beta releases for all changes sinces 2.11.

#### New Features

- Add extra parameter to the validate functions by @anvilpete in #12233
- Add exclude_computed_fields serialization option by @Viicos in #12334
- Add preverse_empty_path URL options by @Viicos in #12336
- Add union_format parameter to JSON Schema generation by @Viicos in #12147
- Add __qualname__ parameter for create_model by @Atry in #12001

#### Fixes

- Do not try to infer name from lambda definitions in pipelines API by @Viicos in #12289
- Use proper namespace for functions in TypeAdapter by @Viicos in #12324
- Use Any for context type annotation in TypeAdapter by @inducer in #12279
- Expose FieldInfo in pydantic.fields.__all__ by @Viicos in #12339
- Respect validation_alias in @validate_call by @Viicos in #12340
- Use Any as context annotation in plugin API by @Viicos in #12341
- Use proper stacklevel in warnings when possible by @Viicos in #12342

#### Packaging

- Update V1 copy to v1.10.24 by @Viicos in #12338

### New Contributors

- @anvilpete made their first contribution in #12233
- @JonathanWindell made their first contribution in #12327
- @inducer made their first contribution in #12279
- @Atry made their first contribution in #12001

## v2.12.0b1 (2025-10-03)

GitHub release

This is the first beta release of the upcoming 2.12 release.

### What's Changed

#### New Features

- Add support for exclude_if at the field level by @andresliszt in #12141
- Add ValidateAs annotation helper by @Viicos in #11942
- Add configuration options for validation and JSON serialization of temporal types by @ollz272 in #12068
- Add support for PEP 728 by @Viicos in #12179
- Add field name in serialization error by @NicolasPllr1 in pydantic-core#1799
- Add option to preserve empty URL paths by @davidhewitt in pydantic-core#1789

#### Changes

- Raise error if an incompatible pydantic-core version is installed by @Viicos in #12196
- Remove runtime warning for experimental features by @Viicos in #12265
- Warn if registering virtual subclasses on Pydantic models by @Viicos in #11669

#### Fixes

- Fix __getattr__() behavior on Pydantic models when a property raised an AttributeError and extra values are present by @raspuchin in #12106
- Add test to prevent regression with Pydantic models used as annotated metadata by @Viicos in #12133
- Allow to use property setters on Pydantic dataclasses with validate_assignment set by @Viicos in #12173
- Fix mypy v2 plugin for upcoming mypy release by @cdce8p in #12209
- Respect custom title in functions JSON Schema by @Viicos in #11892
- Fix ImportString JSON serialization for objects with a name attribute by @chr1sj0nes in #12219
- Do not error on fields overridden by methods in the mypy plugin by @Viicos in #12290

#### Packaging

- Bump pydantic-core to v2.40.1 by @Viicos in #12314

### New Contributors

- @raspuchin made their first contribution in #12106
- @chr1sj0nes made their first contribution in #12219

## v2.12.0a1 (2025-07-26)

GitHub release

This is the first alpha release of the upcoming 2.12 release, which adds initial support for Python 3.14.

### What's Changed

#### New Features

- Add __pydantic_on_complete__() hook that is called once model is fully ready to be used by @DouweM in #11762
- Add initial support for Python 3.14 by @Viicos in #11991
- Add regex patterns to JSON schema for Decimal type by @Dima-Bulavenko in #11987
- Add support for doc attribute on dataclass fields by @Viicos in #12077
- Add experimental MISSING sentinel by @Viicos in #11883

#### Changes

- Allow config and bases to be specified together in create_model() by @Viicos in #11714
- Move some field logic out of the GenerateSchema class by @Viicos in #11733
- Always make use of inspect.getsourcelines() for docstring extraction on Python 3.13 and greater by @Viicos in #11829
- Only support the latest Mypy version by @Viicos in #11832
- Do not implicitly convert after model validators to class methods by @Viicos in #11957
- Refactor FieldInfo creation implementation by @Viicos in #11898
- Make Secret covariant by @bluenote10 in #12008
- Emit warning when field-specific metadata is used in invalid contexts by @Viicos in #12028

#### Fixes

- Properly fetch plain serializer function when serializing default value in JSON Schema by @Viicos in #11721
- Remove generics cache workaround by @Viicos in #11755
- Remove coercion of decimal constraints by @Viicos in #11772
- Fix crash when expanding root type in the mypy plugin by @Viicos in #11735
- Only mark model as complete once all fields are complete by @DouweM in #11759
- Do not provide field_name in validator core schemas by @DouweM in #11761
- Fix issue with recursive generic models by @Viicos in #11775
- Fix qualified name comparison of private attributes during namespace inspection by @karta9821 in #11803
- Make sure Pydantic dataclasses with slots and validate_assignment can be unpickled by @Viicos in #11769
- Traverse function-before schemas during schema gathering by @Viicos in #11801
- Fix check for stdlib dataclasses by @Viicos in #11822
- Check if FieldInfo is complete after applying type variable map by @Viicos in #11855
- Do not delete mock validator/serializer in model_rebuild() by @Viicos in #11890
- Rebuild dataclass fields before schema generation by @Viicos in #11949
- Always store the original field assignment on FieldInfo by @Viicos in #11946
- Do not use deprecated methods as default field values by @Viicos in #11914
- Allow callable discriminator to be applied on PEP 695 type aliases by @Viicos in #11941
- Suppress core schema generation warning when using SkipValidation by @ygsh0816 in #12002
- Do not emit typechecking error for invalid Field() default with validate_default set to True by @Viicos in #11988
- Refactor logic to support Pydantic's Field() function in dataclasses by @Viicos in #12051

#### Packaging

- Update project metadata to use PEP 639 by @Viicos in #11694
- Bump mkdocs-llmstxt to v0.2.0 by @Viicos in #11725
- Bump pydantic-core to v2.35.1 by @Viicos in #11963
- Bump dawidd6/action-download-artifact from 10 to 11 by @dependabot[bot] in #12033
- Bump astral-sh/setup-uv from 5 to 6 by @dependabot[bot] in #11826
- Update mypy to 1.17.0 by @Viicos in #12076

### New Contributors

- @parth-paradkar made their first contribution in #11695
- @dqkqd made their first contribution in #11739
- @fhightower made their first contribution in #11722
- @gbaian10 made their first contribution in #11766
- @DouweM made their first contribution in #11759
- @bowenliang123 made their first contribution in #11719
- @rawwar made their first contribution in #11799
- @karta9821 made their first contribution in #11803
- @jinnovation made their first contribution in #11834
- @zmievsa made their first contribution in #11861
- @Otto-AA made their first contribution in #11860
- @ygsh0816 made their first contribution in #12002
- @lukland made their first contribution in #12015
- @Dima-Bulavenko made their first contribution in #11987
- @GSemikozov made their first contribution in #12050
- @hannah-heywa made their first contribution in #12082

## v2.11.10 (2025-10-04)

GitHub release

### What's Changed

#### Fixes

- Backport v1.10.24 changes by @Viicos

## v2.11.9 (2025-09-13)

GitHub release

### What's Changed

#### Fixes

- Backport v1.10.23 changes by @Viicos

## v2.11.8 (2025-09-13)

GitHub release

### What's Changed

#### Fixes

- Fix mypy plugin for mypy 1.18 by @cdce8p in #12209

## v2.11.7 (2025-06-14)

GitHub release

### What's Changed

#### Fixes

- Copy FieldInfo instance if necessary during FieldInfo build by @Viicos in #11898

## v2.11.6 (2025-06-13)

GitHub release

### What's Changed

#### Fixes

- Rebuild dataclass fields before schema generation by @Viicos in #11949
- Always store the original field assignment on FieldInfo by @Viicos in #11946

## v2.11.5 (2025-05-22)

GitHub release

### What's Changed

#### Fixes

- Check if FieldInfo is complete after applying type variable map by @Viicos in #11855
- Do not delete mock validator/serializer in model_rebuild() by @Viicos in #11890
- Do not duplicate metadata on model rebuild by @Viicos in #11902

## v2.11.4 (2025-04-29)

GitHub release

### What's Changed

#### Changes

- Allow config and bases to be specified together in create_model() by @Viicos in #11714.
This change was backported as it was previously possible (although not meant to be supported)
to provide model_config as a field, which would make it possible to provide both configuration
and bases.

#### Fixes

- Remove generics cache workaround by @Viicos in #11755
- Remove coercion of decimal constraints by @Viicos in #11772
- Fix crash when expanding root type in the mypy plugin by @Viicos in #11735
- Fix issue with recursive generic models by @Viicos in #11775
- Traverse function-before schemas during schema gathering by @Viicos in #11801

#### Packaging

- Bump mkdocs-llmstxt to v0.2.0 by @Viicos in #11725

## v2.11.3 (2025-04-08)

GitHub release

### What's Changed

#### Fixes

- Preserve field description when rebuilding model fields by @Viicos in #11698

#### Packaging

- Update V1 copy to v1.10.21 by @Viicos in #11706

## v2.11.2 (2025-04-03)

GitHub release

### What's Changed

#### Fixes

- Bump pydantic-core to v2.33.1 by @Viicos in #11678
- Make sure __pydantic_private__ exists before setting private attributes by @Viicos in #11666
- Do not override FieldInfo._complete when using field from parent class by @Viicos in #11668
- Provide the available definitions when applying discriminated unions by @Viicos in #11670
- Do not expand root type in the mypy plugin for variables by @Viicos in #11676
- Mention the attribute name in model fields deprecation message by @Viicos in #11674
- Properly validate parameterized mappings by @Viicos in #11658

## v2.11.1 (2025-03-28)

GitHub release

### What's Changed

#### Fixes

- Do not override 'definitions-ref' schemas containing serialization schemas or metadata by @Viicos in #11644

## v2.11.0 (2025-03-27)

GitHub release

### What's Changed

Pydantic v2.11 is a version strongly focused on build time performance of Pydantic models (and core schema generation in general).
See the blog post for more details.

#### New Features

- Add encoded_string() method to the URL types by @YassinNouh21 in #11580
- Add support for defer_build with @validate_call decorator by @Viicos in #11584
- Allow @with_config decorator to be used with keyword arguments by @Viicos in #11608
- Simplify customization of default value inclusion in JSON Schema generation by @Viicos in #11634
- Add generate_arguments_schema() function by @Viicos in #11572

#### Fixes

- Allow generic typed dictionaries to be used for unpacked variadic keyword parameters by @Viicos in #11571
- Fix runtime error when computing model string representation involving cached properties and self-referenced models by @Viicos in #11579
- Preserve other steps when using the ellipsis in the pipeline API by @Viicos in #11626
- Fix deferred discriminator application logic by @Viicos in #11591

#### Packaging

- Bump pydantic-core to v2.33.0 by @Viicos in #11631

### New Contributors

- @cmenon12 made their first contribution in #11562
- @Jeukoh made their first contribution in #11611

## v2.11.0b2 (2025-03-17)

GitHub release

### What's Changed

#### New Features

- Add experimental support for free threading by @Viicos in #11516

#### Fixes

- Fix NotRequired qualifier not taken into account in stringified annotation by @Viicos in #11559

#### Packaging

- Bump pydantic-core to v2.32.0 by @Viicos in #11567

### New Contributors

- @joren485 made their first contribution in #11547

## v2.11.0b1 (2025-03-06)

GitHub release

### What's Changed

#### New Features

- Support unsubstituted type variables with both a default and a bound or constraints by @FyZzyss in https://github.com/pydantic/pydantic/pull/10789
- Add a default_factory_takes_validated_data property to FieldInfo by @Viicos in https://github.com/pydantic/pydantic/pull/11034
- Raise a better error when a generic alias is used inside type[] by @Viicos in https://github.com/pydantic/pydantic/pull/11088
- Properly support PEP 695 generics syntax by @Viicos in https://github.com/pydantic/pydantic/pull/11189
- Properly support type variable defaults by @Viicos in https://github.com/pydantic/pydantic/pull/11332
- Add support for validating v6, v7, v8 UUIDs by @astei in https://github.com/pydantic/pydantic/pull/11436
- Improve alias configuration APIs by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11468

#### Changes

- Rework create_model field definitions format by @Viicos in https://github.com/pydantic/pydantic/pull/11032
- Raise a deprecation warning when a field is annotated as final with a default value by @Viicos in https://github.com/pydantic/pydantic/pull/11168
- Deprecate accessing model_fields and model_computed_fields on instances by @Viicos in https://github.com/pydantic/pydantic/pull/11169
- Breaking Change: Move core schema generation logic for path types inside the GenerateSchema class by @sydney-runkle in https://github.com/pydantic/pydantic/pull/10846
- Remove Python 3.8 Support by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11258
- Optimize calls to get_type_ref by @Viicos in https://github.com/pydantic/pydantic/pull/10863
- Disable pydantic-core core schema validation by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11271

#### Performance

- Only evaluate FieldInfo annotations if required during schema building by @Viicos in https://github.com/pydantic/pydantic/pull/10769
- Improve __setattr__ performance of Pydantic models by caching setter functions by @MarkusSintonen in https://github.com/pydantic/pydantic/pull/10868
- Improve annotation application performance by @Viicos in https://github.com/pydantic/pydantic/pull/11186
- Improve performance of _typing_extra module by @Viicos in https://github.com/pydantic/pydantic/pull/11255
- Refactor and optimize schema cleaning logic by @Viicos in https://github.com/pydantic/pydantic/pull/11244
- Create a single dictionary when creating a CoreConfig instance by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11384
- Bump pydantic-core and thus use SchemaValidator and SchemaSerializer caching by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11402
- Reuse cached core schemas for parametrized generic Pydantic models by @MarkusSintonen in https://github.com/pydantic/pydantic/pull/11434

#### Fixes

- Improve TypeAdapter instance repr by @sydney-runkle in https://github.com/pydantic/pydantic/pull/10872
- Use the correct frame when instantiating a parametrized TypeAdapter by @Viicos in https://github.com/pydantic/pydantic/pull/10893
- Infer final fields with a default value as class variables in the mypy plugin by @Viicos in https://github.com/pydantic/pydantic/pull/11121
- Recursively unpack Literal values if using PEP 695 type aliases by @Viicos in https://github.com/pydantic/pydantic/pull/11114
- Override __subclasscheck__ on ModelMetaclass to avoid memory leak and performance issues by @Viicos in https://github.com/pydantic/pydantic/pull/11116
- Remove unused _extract_get_pydantic_json_schema() parameter by @Viicos in https://github.com/pydantic/pydantic/pull/11155
- Improve discriminated union error message for invalid union variants by @Viicos in https://github.com/pydantic/pydantic/pull/11161
- Unpack PEP 695 type aliases if using the Annotated form by @Viicos in https://github.com/pydantic/pydantic/pull/11109
- Add missing stacklevel in deprecated_instance_property warning by @Viicos in https://github.com/pydantic/pydantic/pull/11200
- Copy WithJsonSchema schema to avoid sharing mutated data by @thejcannon in https://github.com/pydantic/pydantic/pull/11014
- Do not cache parametrized models when in the process of parametrizing another model by @Viicos in https://github.com/pydantic/pydantic/pull/10704
- Add discriminated union related metadata entries to the CoreMetadata definition by @Viicos in https://github.com/pydantic/pydantic/pull/11216
- Consolidate schema definitions logic in the _Definitions class by @Viicos in https://github.com/pydantic/pydantic/pull/11208
- Support initializing root model fields with values of the root type in the mypy plugin by @Viicos in https://github.com/pydantic/pydantic/pull/11212
- Fix various issues with dataclasses and use_attribute_docstrings by @Viicos in https://github.com/pydantic/pydantic/pull/11246
- Only compute normalized decimal places if necessary in decimal_places_validator by @misrasaurabh1 in https://github.com/pydantic/pydantic/pull/11281
- Add support for validation_alias in the mypy plugin by @Viicos in https://github.com/pydantic/pydantic/pull/11295
- Fix JSON Schema reference collection with "examples" keys by @Viicos in https://github.com/pydantic/pydantic/pull/11305
- Do not transform model serializer functions as class methods in the mypy plugin by @Viicos in https://github.com/pydantic/pydantic/pull/11298
- Simplify GenerateJsonSchema.literal_schema() implementation by @misrasaurabh1 in https://github.com/pydantic/pydantic/pull/11321
- Add additional allowed schemes for ClickHouseDsn by @Maze21127 in https://github.com/pydantic/pydantic/pull/11319
- Coerce decimal constraints to Decimal instances by @Viicos in https://github.com/pydantic/pydantic/pull/11350
- Use the correct JSON Schema mode when handling function schemas by @Viicos in https://github.com/pydantic/pydantic/pull/11367
- Improve exception message when encountering recursion errors during type evaluation by @Viicos in https://github.com/pydantic/pydantic/pull/11356
- Always include additionalProperties: True for arbitrary dictionary schemas by @austinyu in https://github.com/pydantic/pydantic/pull/11392
- Expose fallback parameter in serialization methods by @Viicos in https://github.com/pydantic/pydantic/pull/11398
- Fix path serialization behavior by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11416
- Do not reuse validators and serializers during model rebuild by @Viicos in https://github.com/pydantic/pydantic/pull/11429
- Collect model fields when rebuilding a model by @Viicos in https://github.com/pydantic/pydantic/pull/11388
- Allow cached properties to be altered on frozen models by @Viicos in https://github.com/pydantic/pydantic/pull/11432
- Fix tuple serialization for Sequence types by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11435
- Fix: do not check for __get_validators__ on classes where __get_pydantic_core_schema__ is also defined by @tlambert03 in https://github.com/pydantic/pydantic/pull/11444
- Allow callable instances to be used as serializers by @Viicos in https://github.com/pydantic/pydantic/pull/11451
- Improve error thrown when overriding field with a property by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11459
- Fix JSON Schema generation with referenceable core schemas holding JSON metadata by @Viicos in https://github.com/pydantic/pydantic/pull/11475
- Support strict specification on union member types by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11481
- Implicitly set validate_by_name to True when validate_by_alias is False by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11503
- Change type of Any when synthesizing BaseSettings.__init__ signature in the mypy plugin by @Viicos in https://github.com/pydantic/pydantic/pull/11497
- Support type variable defaults referencing other type variables by @Viicos in https://github.com/pydantic/pydantic/pull/11520
- Fix ValueError on year zero by @davidhewitt in https://github.com/pydantic/pydantic-core/pull/1583
- dataclass InitVar shouldn't be required on serialization by @sydney-runkle in https://github.com/pydantic/pydantic-core/pull/1602

#### Packaging

- Add a check_pydantic_core_version() function by @Viicos in https://github.com/pydantic/pydantic/pull/11324
- Remove greenlet development dependency by @Viicos in https://github.com/pydantic/pydantic/pull/11351
- Use the typing-inspection library by @Viicos in https://github.com/pydantic/pydantic/pull/11479
- Bump pydantic-core to v2.31.1 by @sydney-runkle in https://github.com/pydantic/pydantic/pull/11526

## New Contributors

- @FyZzyss made their first contribution in https://github.com/pydantic/pydantic/pull/10789
- @tamird made their first contribution in https://github.com/pydantic/pydantic/pull/10948
- @felixxm made their first contribution in https://github.com/pydantic/pydantic/pull/11077
- @alexprabhat99 made their first contribution in https://github.com/pydantic/pydantic/pull/11082
- @Kharianne made their first contribution in https://github.com/pydantic/pydantic/pull/11111
- @mdaffad made their first contribution in https://github.com/pydantic/pydantic/pull/11177
- @thejcannon made their first contribution in https://github.com/pydantic/pydantic/pull/11014
- @thomasfrimannkoren made their first contribution in https://github.com/pydantic/pydantic/pull/11251
- @usernameMAI made their first contribution in https://github.com/pydantic/pydantic/pull/11275
- @ananiavito made their first contribution in https://github.com/pydantic/pydantic/pull/11302
- @pawamoy made their first contribution in https://github.com/pydantic/pydantic/pull/11311
- @Maze21127 made their first contribution in https://github.com/pydantic/pydantic/pull/11319
- @kauabh made their first contribution in https://github.com/pydantic/pydantic/pull/11369
- @jaceklaskowski made their first contribution in https://github.com/pydantic/pydantic/pull/11353
- @tmpbeing made their first contribution in https://github.com/pydantic/pydantic/pull/11375
- @petyosi made their first contribution in https://github.com/pydantic/pydantic/pull/11405
- @austinyu made their first contribution in https://github.com/pydantic/pydantic/pull/11392
- @mikeedjones made their first contribution in https://github.com/pydantic/pydantic/pull/11402
- @astei made their first contribution in https://github.com/pydantic/pydantic/pull/11436
- @dsayling made their first contribution in https://github.com/pydantic/pydantic/pull/11522
- @sobolevn made their first contribution in https://github.com/pydantic/pydantic-core/pull/1645

## v2.11.0a2 (2025-02-10)

GitHub release

### What's Changed

Pydantic v2.11 is a version strongly focused on build time performance of Pydantic models (and core schema generation in general).
This is another early alpha release, meant to collect early feedback from users having issues with core schema builds.

#### Performance

- Create a single dictionary when creating a CoreConfig instance by @sydney-runkle in #11384

#### Fixes

- Use the correct JSON Schema mode when handling function schemas by @Viicos in #11367
- Fix JSON Schema reference logic with examples keys by @Viicos in #11366
- Improve exception message when encountering recursion errors during type evaluation by @Viicos in #11356
- Always include additionalProperties: True for arbitrary dictionary schemas by @austinyu in #11392
- Expose fallback parameter in serialization methods by @Viicos in #11398
- Fix path serialization behavior by @sydney-runkle in #11416

#### Packaging

- Bump ruff from 0.9.2 to 0.9.5 by @Viicos in #11407
- Bump pydantic-core to v2.29.0 by @mikeedjones in #11402
- Use locally-built rust with symbols & pgo by @davidhewitt in #11403

### New Contributors

- @kauabh made their first contribution in #11369
- @jaceklaskowski made their first contribution in #11353
- @tmpbeing made their first contribution in #11375
- @petyosi made their first contribution in #11405
- @austinyu made their first contribution in #11392
- @mikeedjones made their first contribution in #11402

## v2.11.0a1 (2025-01-30)

GitHub release

### What's Changed

Pydantic v2.11 is a version strongly focused on build time performance of Pydantic models (and core schema generation in general).
This is an early alpha release, meant to collect early feedback from users having issues with core schema builds.

#### New Features

- Support unsubstituted type variables with both a default and a bound or constraints by @FyZzyss in #10789
- Add a default_factory_takes_validated_data property to FieldInfo by @Viicos in #11034
- Raise a better error when a generic alias is used inside type[] by @Viicos in #11088
- Properly support PEP 695 generics syntax by @Viicos in #11189
- Properly support type variable defaults by @Viicos in #11332

#### Changes

- Rework create_model field definitions format by @Viicos in #11032
- Raise a deprecation warning when a field is annotated as final with a default value by @Viicos in #11168
- Deprecate accessing model_fields and model_computed_fields on instances by @Viicos in #11169
- Move core schema generation logic for path types inside the GenerateSchema class by @sydney-runkle in #10846
- Move deque schema gen to GenerateSchema class by @sydney-runkle in #11239
- Move Mapping schema gen to GenerateSchema to complete removal of prepare_annotations_for_known_type workaround by @sydney-runkle in #11247
- Remove Python 3.8 Support by @sydney-runkle in #11258
- Disable pydantic-core core schema validation by @sydney-runkle in #11271

#### Performance

- Only evaluate FieldInfo annotations if required during schema building by @Viicos in #10769
- Optimize calls to get_type_ref by @Viicos in #10863
- Improve __setattr__ performance of Pydantic models by caching setter functions by @MarkusSintonen in #10868
- Improve annotation application performance by @Viicos in #11186
- Improve performance of _typing_extra module by @Viicos in #11255
- Refactor and optimize schema cleaning logic by @Viicos and @MarkusSintonen in #11244

#### Fixes

- Add validation tests for _internal/_validators.py by @tkasuz in #10763
- Improve TypeAdapter instance repr by @sydney-runkle in #10872
- Revert "ci: use locally built pydantic-core with debug symbols by @sydney-runkle in #10942
- Re-enable all FastAPI tests by @tamird in #10948
- Fix typo in HISTORY.md. by @felixxm in #11077
- Infer final fields with a default value as class variables in the mypy plugin by @Viicos in #11121
- Recursively unpack Literal values if using PEP 695 type aliases by @Viicos in #11114
- Override __subclasscheck__ on ModelMetaclass to avoid memory leak and performance issues by @Viicos in #11116
- Remove unused _extract_get_pydantic_json_schema() parameter by @Viicos in #11155
- Add FastAPI and SQLModel to third-party tests by @sydney-runkle in #11044
- Fix conditional expressions syntax for third-party tests by @Viicos in #11162
- Move FastAPI tests to third-party workflow by @Viicos in #11164
- Improve discriminated union error message for invalid union variants by @Viicos in #11161
- Unpack PEP 695 type aliases if using the Annotated form by @Viicos in #11109
- Include openapi-python-client check in issue creation for third-party failures, use main branch by @sydney-runkle in #11182
- Add pandera third-party tests by @Viicos in #11193
- Add ODMantic third-party tests by @sydney-runkle in #11197
- Add missing stacklevel in deprecated_instance_property warning by @Viicos in #11200
- Copy WithJsonSchema schema to avoid sharing mutated data by @thejcannon in #11014
- Do not cache parametrized models when in the process of parametrizing another model by @Viicos in #10704
- Re-enable Beanie third-party tests by @Viicos in #11214
- Add discriminated union related metadata entries to the CoreMetadata definition by @Viicos in #11216
- Consolidate schema definitions logic in the _Definitions class by @Viicos in #11208
- Support initializing root model fields with values of the root type in the mypy plugin by @Viicos in #11212
- Fix various issues with dataclasses and use_attribute_docstrings by @Viicos in #11246
- Only compute normalized decimal places if necessary in decimal_places_validator by @misrasaurabh1 in #11281
- Fix two misplaced sentences in validation errors documentation by @ananiavito in #11302
- Fix mkdocstrings inventory example in documentation by @pawamoy in #11311
- Add support for validation_alias in the mypy plugin by @Viicos in #11295
- Do not transform model serializer functions as class methods in the mypy plugin by @Viicos in #11298
- Simplify GenerateJsonSchema.literal_schema() implementation by @misrasaurabh1 in #11321
- Add additional allowed schemes for ClickHouseDsn by @Maze21127 in #11319
- Coerce decimal constraints to Decimal instances by @Viicos in #11350
- Fix ValueError on year zero by @davidhewitt in pydantic-core#1583

#### Packaging

- Bump dawidd6/action-download-artifact from 6 to 7 by @dependabot in #11018
- Re-enable memray related tests on Python 3.12+ by @Viicos in #11191
- Bump astral-sh/setup-uv to 5 by @dependabot in #11205
- Bump ruff to v0.9.0 by @sydney-runkle in #11254
- Regular uv.lock deps update by @sydney-runkle in #11333
- Add a check_pydantic_core_version() function by @Viicos in #11324
- Remove greenlet development dependency by @Viicos in #11351
- Bump pydantic-core to v2.28.0 by @Viicos in #11364

### New Contributors

- @FyZzyss made their first contribution in #10789
- @tamird made their first contribution in #10948
- @felixxm made their first contribution in #11077
- @alexprabhat99 made their first contribution in #11082
- @Kharianne made their first contribution in #11111
- @mdaffad made their first contribution in #11177
- @thejcannon made their first contribution in #11014
- @thomasfrimannkoren made their first contribution in #11251
- @usernameMAI made their first contribution in #11275
- @ananiavito made their first contribution in #11302
- @pawamoy made their first contribution in #11311
- @Maze21127 made their first contribution in #11319

## v2.10.6 (2025-01-23)

GitHub release

### What's Changed

#### Fixes

- Fix JSON Schema reference collection with 'examples' keys by @Viicos in #11325
- Fix url python serialization by @sydney-runkle in #11331

## v2.10.5 (2025-01-08)

GitHub release

### What's Changed

#### Fixes

- Remove custom MRO implementation of Pydantic models by @Viicos in #11184
- Fix URL serialization for unions by @sydney-runkle in #11233

## v2.10.4 (2024-12-18)

GitHub release

### What's Changed

#### Fixes

- Fix for comparison of AnyUrl objects by @alexprabhat99 in #11082
- Properly fetch PEP 695 type params for functions, do not fetch annotations from signature by @Viicos in #11093
- Include JSON Schema input core schema in function schemas by @Viicos in #11085
- Add len to _BaseUrl to avoid TypeError by @Kharianne in #11111
- Make sure the type reference is removed from the seen references by @Viicos in #11143

### New Contributors

- @FyZzyss made their first contribution in #10789
- @tamird made their first contribution in #10948
- @felixxm made their first contribution in #11077
- @alexprabhat99 made their first contribution in #11082
- @Kharianne made their first contribution in #11111

#### Packaging

- Bump pydantic-core to v2.27.2 by @davidhewitt in #11138

## v2.10.3 (2024-12-03)

GitHub release

### What's Changed

#### Fixes

- Set fields when defer_build is set on Pydantic dataclasses by @Viicos in #10984
- Do not resolve the JSON Schema reference for dict core schema keys by @Viicos in #10989
- Use the globals of the function when evaluating the return type for PlainSerializer and WrapSerializer functions by @Viicos in #11008
- Fix host required enforcement for urls to be compatible with v2.9 behavior by @sydney-runkle in #11027
- Add a default_factory_takes_validated_data property to FieldInfo by @Viicos in #11034
- Fix url json schema in serialization mode by @sydney-runkle in #11035

## v2.10.2 (2024-11-25)

GitHub release

### What's Changed

#### Fixes

- Only evaluate FieldInfo annotations if required during schema building by @Viicos in #10769
- Do not evaluate annotations for private fields by @Viicos in #10962
- Support serialization as any for Secret types and Url types by @sydney-runkle in #10947
- Fix type hint of Field.default to be compatible with Python 3.8 and 3.9 by @Viicos in #10972
- Add hashing support for URL types by @sydney-runkle in #10975
- Hide BaseModel.__replace__ definition from type checkers by @Viicos in #10979

## v2.10.1 (2024-11-21)

GitHub release

### What's Changed

#### Fixes

- Use the correct frame when instantiating a parametrized TypeAdapter by @Viicos in #10893
- Relax check for validated data in default_factory utils by @sydney-runkle in #10909
- Fix type checking issue with model_fields and model_computed_fields by @sydney-runkle in #10911
- Use the parent configuration during schema generation for stdlib dataclasses by @sydney-runkle in #10928
- Use the globals of the function when evaluating the return type of serializers and computed_fields by @Viicos in #10929
- Fix URL constraint application by @sydney-runkle in #10922
- Fix URL equality with different validation methods by @sydney-runkle in #10934
- Fix JSON schema title when specified as '' by @sydney-runkle in #10936
- Fix python mode serialization for complex inference by @sydney-runkle in pydantic-core#1549

#### Packaging

- Bump pydantic-core version to v2.27.1 by @sydney-runkle in #10938

### New Contributors

## v2.10.0 (2024-11-20)

The code released in v2.10.0 is practically identical to that of v2.10.0b2.

GitHub release

See the v2.10 release blog post for the highlights!

### What's Changed

#### New Features

- Support fractions.Fraction by @sydney-runkle in #10318
- Support Hashable for json validation by @sydney-runkle in #10324
- Add a SocketPath type for linux systems by @theunkn0wn1 in #10378
- Allow arbitrary refs in JSON schema examples by @sydney-runkle in #10417
- Support defer_build for Pydantic dataclasses by @Viicos in #10313
- Adding v1 / v2 incompatibility warning for nested v1 model by @sydney-runkle in #10431
- Add support for unpacked TypedDict to type hint variadic keyword arguments with @validate_call by @Viicos in #10416
- Support compiled patterns in protected_namespaces by @sydney-runkle in #10522
- Add support for propertyNames in JSON schema by @FlorianSW in #10478
- Adding __replace__ protocol for Python 3.13+ support by @sydney-runkle in #10596
- Expose public sort method for JSON schema generation by @sydney-runkle in #10595
- Add runtime validation of @validate_call callable argument by @kc0506 in #10627
- Add experimental_allow_partial support by @samuelcolvin in #10748
- Support default factories taking validated data as an argument by @Viicos in #10678
- Allow subclassing ValidationError and PydanticCustomError by @Youssefares in pydantic/pydantic-core#1413
- Add trailing-strings support to experimental_allow_partial by @sydney-runkle in #10825
- Add rebuild() method for TypeAdapter and simplify defer_build patterns by @sydney-runkle in #10537
- Improve TypeAdapter instance repr by @sydney-runkle in #10872

#### Changes

- Don't allow customization of SchemaGenerator until interface is more stable by @sydney-runkle in #10303
- Cleanly defer_build on TypeAdapters, removing experimental flag by @sydney-runkle in #10329
- Fix mro of generic subclass by @kc0506 in #10100
- Strip whitespaces on JSON Schema title generation by @sydney-runkle in #10404
- Use b64decode and b64encode for Base64Bytes type by @sydney-runkle in #10486
- Relax protected namespace config default by @sydney-runkle in #10441
- Revalidate parametrized generics if instance's origin is subclass of OG class by @sydney-runkle in #10666
- Warn if configuration is specified on the @dataclass decorator and with the __pydantic_config__ attribute by @sydney-runkle in #10406
- Recommend against using Ellipsis (...) with Field by @Viicos in #10661
- Migrate to subclassing instead of annotated approach for pydantic url types by @sydney-runkle in #10662
- Change JSON schema generation of Literals and Enums by @Viicos in #10692
- Simplify unions involving Any or Never when replacing type variables by @Viicos in #10338
- Do not require padding when decoding base64 bytes by @bschoenmaeckers in pydantic/pydantic-core#1448
- Support dates all the way to 1BC by @changhc in pydantic/speedate#77

#### Performance

- Schema cleaning: skip unnecessary copies during schema walking by @Viicos in #10286
- Refactor namespace logic for annotations evaluation by @Viicos in #10530
- Improve email regexp on edge cases by @AlekseyLobanov in #10601
- CoreMetadata refactor with an emphasis on documentation, schema build time performance, and reducing complexity by @sydney-runkle in #10675

#### Packaging

- Bump pydantic-core to v2.27.0 by @sydney-runkle in #10825
- Replaced pdm with uv by @frfahim in #10727

#### Fixes

- Remove guarding check on computed_field with field_serializer by @nix010 in #10390
- Fix Predicate issue in v2.9.0 by @sydney-runkle in #10321
- Fixing annotated-types bound by @sydney-runkle in #10327
- Turn tzdata install requirement into optional timezone dependency by @jakob-keller in #10331
- Use correct types namespace when building namedtuple core schemas by @Viicos in #10337
- Fix evaluation of stringified annotations during namespace inspection by @Viicos in #10347
- Fix IncEx type alias definition by @Viicos in #10339
- Do not error when trying to evaluate annotations of private attributes by @Viicos in #10358
- Fix nested type statement by @kc0506 in #10369
- Improve typing of ModelMetaclass.mro by @Viicos in #10372
- Fix class access of deprecated computed_fields by @Viicos in #10391
- Make sure inspect.iscoroutinefunction works on coroutines decorated with @validate_call by @MovisLi in #10374
- Fix NameError when using validate_call with PEP 695 on a class by @kc0506 in #10380
- Fix ZoneInfo with various invalid types by @sydney-runkle in #10408
- Fix PydanticUserError on empty model_config with annotations by @cdwilson in #10412
- Fix variance issue in _IncEx type alias, only allow True by @Viicos in #10414
- Fix serialization schema generation when using PlainValidator by @Viicos in #10427
- Fix schema generation error when serialization schema holds references by @Viicos in #10444
- Inline references if possible when generating schema for json_schema_input_type by @Viicos in #10439
- Fix recursive arguments in Representation by @Viicos in #10480
- Fix representation for builtin function types by @kschwab in #10479
- Add python validators for decimal constraints (max_digits and decimal_places) by @sydney-runkle in #10506
- Only fetch __pydantic_core_schema__ from the current class during schema generation by @Viicos in #10518
- Fix stacklevel on deprecation warnings for BaseModel by @sydney-runkle in #10520
- Fix warning stacklevel in BaseModel.__init__ by @Viicos in #10526
- Improve error handling for in-evaluable refs for discriminator application by @sydney-runkle in #10440
- Change the signature of ConfigWrapper.core_config to take the title directly by @Viicos in #10562
- Do not use the previous config from the stack for dataclasses without config by @Viicos in #10576
- Fix serialization for IP types with mode='python' by @sydney-runkle in #10594
- Support constraint application for Base64Etc types by @sydney-runkle in #10584
- Fix validate_call ignoring Field in Annotated by @kc0506 in #10610
- Raise an error when Self is invalid by @kc0506 in #10609
- Using core_schema.InvalidSchema instead of metadata injection + checks by @sydney-runkle in #10523
- Tweak type alias logic by @kc0506 in #10643
- Support usage of type with typing.Self and type aliases by @kc0506 in #10621
- Use overloads for Field and PrivateAttr functions by @Viicos in #10651
- Clean up the mypy plugin implementation by @Viicos in #10669
- Properly check for typing_extensions variant of TypeAliasType by @Daraan in #10713
- Allow any mapping in BaseModel.model_copy() by @Viicos in #10751
- Fix isinstance behavior for urls by @sydney-runkle in #10766
- Ensure cached_property can be set on Pydantic models by @Viicos in #10774
- Fix equality checks for primitives in literals by @sydney-runkle in pydantic/pydantic-core#1459
- Properly enforce host_required for URLs by @Viicos in pydantic/pydantic-core#1488
- Fix when coerce_numbers_to_str enabled and string has invalid Unicode character by @andrey-berenda in pydantic/pydantic-core#1515
- Fix serializing complex values in Enums by @changhc in pydantic/pydantic-core#1524
- Refactor _typing_extra module by @Viicos in #10725
- Support intuitive equality for urls by @sydney-runkle in #10798
- Add bytearray to TypeAdapter.validate_json signature by @samuelcolvin in #10802
- Ensure class access of method descriptors is performed when used as a default with Field by @Viicos in #10816
- Fix circular import with validate_call by @sydney-runkle in #10807
- Fix error when using type aliases referencing other type aliases by @Viicos in #10809
- Fix IncEx type alias to be compatible with mypy by @Viicos in #10813
- Make __signature__ a lazy property, do not deepcopy defaults by @Viicos in #10818
- Make __signature__ lazy for dataclasses, too by @sydney-runkle in #10832
- Subclass all single host url classes from AnyUrl to preserve behavior from v2.9 by @sydney-runkle in #10856

### New Contributors

- @jakob-keller made their first contribution in #10331
- @MovisLi made their first contribution in #10374
- @joaopalmeiro made their first contribution in #10405
- @theunkn0wn1 made their first contribution in #10378
- @cdwilson made their first contribution in #10412
- @dlax made their first contribution in #10421
- @kschwab made their first contribution in #10479
- @santibreo made their first contribution in #10453
- @FlorianSW made their first contribution in #10478
- @tkasuz made their first contribution in #10555
- @AlekseyLobanov made their first contribution in #10601
- @NiclasvanEyk made their first contribution in #10667
- @mschoettle made their first contribution in #10677
- @Daraan made their first contribution in #10713
- @k4nar made their first contribution in #10736
- @UriyaHarpeness made their first contribution in #10740
- @frfahim made their first contribution in #10727

## v2.10.0b2 (2024-11-13)

Pre-release, see the GitHub release for details.

## v2.10.0b1 (2024-11-06)

Pre-release, see the GitHub release for details.

... see here for earlier changes.
