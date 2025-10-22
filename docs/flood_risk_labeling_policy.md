
# Flood Risk Labeling Policy Document

## Overview
This document defines the labeling policy for the Flood Risk ML Dataset, establishing clear rules for classifying road segments as safe (1) or unsafe (0) based on flood risk factors.

## Risk Factors and Thresholds

### 1. Flood Hazard Status
- **Level 0**: No flood hazard (safe baseline)
- **Level 1**: Low flood hazard (caution required)
- **Level 2**: Medium flood hazard (high risk)
- **Level 3**: High flood hazard (extreme risk)

### 2. Rainfall Intensity (3-hour windows)
- **0-10 mm/3h**: Light rain (safe)
- **10-25 mm/3h**: Moderate rain (caution)
- **25-50 mm/3h**: Heavy rain (high risk)
- **50-100 mm/3h**: Extreme rain (very high risk)
- **100+ mm/3h**: Flood-triggering rain (extreme risk)

### 3. Distance to River
- **0-50m**: Very close (high risk)
- **50-100m**: Close (moderate-high risk)
- **100-200m**: Moderate distance (moderate risk)
- **200-500m**: Far (low-moderate risk)
- **500-1000m**: Very far (low risk)
- **1000m+**: Safe distance (very low risk)

### 4. Elevation
- **<0m**: Below sea level (extreme risk)
- **0-5m**: Very low (high risk)
- **5-10m**: Low (moderate-high risk)
- **10-20m**: Moderate (low-moderate risk)
- **20m+**: High (low risk)

### 5. Typhoon Presence
- **No typhoon**: Baseline risk
- **Typhoon present**: Increased risk multiplier

## Labeling Rules

### UNSAFE (0) - High Risk Conditions
1. hazard_status >= 3 (extreme flood hazard)
2. hazard_status >= 2 AND rainfall_mm_3h >= 100 (high hazard + extreme rain)
3. hazard_status >= 1 AND rainfall_mm_3h >= 50 AND dist_to_river <= 100 (any hazard + heavy rain + close to river)
4. elevation <= 5 AND dist_to_river <= 50 AND tracks != "" (low elevation + very close to river + typhoon)
5. rainfall_mm_3h >= 100 AND dist_to_river <= 200 (extreme rain + close to river)

### SAFE (1) - Low Risk Conditions
1. hazard_status == 0 AND rainfall_mm_3h < 25 (no hazard + light rain)
2. hazard_status <= 1 AND elevation >= 10 AND dist_to_river >= 500 (low hazard + high elevation + far from river)
3. hazard_status == 0 AND elevation >= 5 AND dist_to_river >= 200 (no hazard + moderate elevation + far from river)
4. rainfall_mm_3h < 10 AND dist_to_river >= 1000 (very light rain + very far from river)
5. elevation >= 20 (very high elevation regardless of other factors)

### BOUNDARY CASES
For cases not explicitly covered by the above rules, the policy defaults to **UNSAFE (0)** for a conservative approach to public safety.

## Implementation Notes
- The labeling function prioritizes public safety with a conservative approach
- Boundary cases are resolved in favor of caution
- The policy can be adjusted based on local conditions and historical data
- Regular review and updates are recommended based on model performance and real-world outcomes

## Quality Assurance
- All labels are validated against the defined rules
- Regular audits ensure consistency
- Performance metrics track labeling accuracy
- Feedback loops enable policy refinement
