# PlanetaryComputerWrapper

## Summary

Currently works on queries based on:
- datasets
- locations (by given bbox or by intersection with given polygon)
- time_ranges
- assets
- extensions + properties

Currently provides:
- satelite imagery
- time vs. given extension:property plots in Matplotlib

Work in progress for queries related to:
- including more specific support for datasets such as:
  - NASADEM (topographic data)
  - NEX-GDDP-CMIP6 (climate scenarios)
  - JRC-GSW (surface water levels)
  - Daymet (temperature changes)
