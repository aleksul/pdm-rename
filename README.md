# pdm-rename

This plugin allows to dynamically rename folders during the build stage.

## Installation

```bash
pdm self add pdm-rename
```

## Use it

Specify `rename` dictionary in `[tool.pdm]` section.

```toml
[tool.pdm]
rename  = { "a/b" = "c/d" }
```

If you want the folder to be included in your build, don't forget to specify `build.includes`.

```toml
[tool.pdm.build]
includes = ["c"]
```
