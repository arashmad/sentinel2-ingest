from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field


class AoiQualityMetrics(BaseModel):
    """AOI-level pixel quality metrics for a candidate scene.

    Counts are expected to be calculated from scene classification / mask data by a provider
    implementation. This model only stores normalized, provider-independent results.
    """

    model_config = ConfigDict(frozen=True)

    total_pixel_count: int = Field(ge=0)
    valid_data_pixel_count: int = Field(ge=0)

    usable_pixel_count: int = Field(ge=0)
    cloud_pixel_count: int = Field(ge=0)
    shadow_pixel_count: int = Field(ge=0)
    snow_pixel_count: int = Field(ge=0)
    no_data_pixel_count: int = Field(ge=0)
    defective_pixel_count: int = Field(ge=0)
    dark_area_pixel_count: int = Field(ge=0)
    unclassified_pixel_count: int = Field(ge=0)

    @computed_field
    @property
    def usable_pixel_ratio(self) -> float:
        return _safe_ratio(self.usable_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def cloud_pixel_ratio(self) -> float:
        return _safe_ratio(self.cloud_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def shadow_pixel_ratio(self) -> float:
        return _safe_ratio(self.shadow_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def snow_pixel_ratio(self) -> float:
        return _safe_ratio(self.snow_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def no_data_ratio(self) -> float:
        return _safe_ratio(self.no_data_pixel_count, self.total_pixel_count)

    @computed_field
    @property
    def defective_pixel_ratio(self) -> float:
        return _safe_ratio(self.defective_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def dark_area_pixel_ratio(self) -> float:
        return _safe_ratio(self.dark_area_pixel_count, self.valid_data_pixel_count)

    @computed_field
    @property
    def unclassified_pixel_ratio(self) -> float:
        return _safe_ratio(self.unclassified_pixel_count, self.valid_data_pixel_count)


def _safe_ratio(value: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return value / denominator