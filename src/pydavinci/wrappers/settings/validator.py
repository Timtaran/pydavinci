from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel, field_validator, FieldValidationInfo, model_validator

import pydavinci.logger as log
from pydavinci.wrappers.settings.map import SETTINGS_MAP, super_scale_transform

_ANY = Optional[Union[str, int, bool]]


class BaseConfig(BaseModel):  # type: ignore
    @field_validator("*", mode="before")
    def str_none_to_none(cls, value: _ANY) -> _ANY:  # noqa: B902
        # Special case here before everything
        # There are some "None" strings in the data. We want to alter them to the Python None
        # so Pydantic understands it
        if value == "None" or value == "":
            return None
        return value

    @model_validator(mode="after")
    def set_prop_validator(cls, values: "BaseConfig") -> "BaseConfig":
        # This is called on all values assignment
        if not getattr(values, "_selfvalidate", False):
            log.debug("Not sending to Resolve yet.")
            return values

        # Here we check if it's superscale, which needs a different transform from/to Resolve
        # we also check if _selfvalidate is False, if it is, it means we're initializing the
        # class and then we just return the value.

        # If _selfvalidate is True, we then see what transform we need to use
        # in the map.py file, which has a dict of the Fields' Aliases to which callable they need to pass through
        # We then pass to the Resolve API the Alias with the right transform function applied
        for field_name, field_value in values.__dict__.items():
            if field_name in SETTINGS_MAP:
                log.debug(f"Setting '{field_name}' to {field_value}")
                call: Callable[[Any], Any] = SETTINGS_MAP[field_name]
                getattr(values, "_obj").SetSetting(field_name, call(field_value))

        return values

    class Config:
        extra = "forbid"
        validate_assignment = True
        allow_population_by_field_name = True
        underscore_attrs_are_private = False
