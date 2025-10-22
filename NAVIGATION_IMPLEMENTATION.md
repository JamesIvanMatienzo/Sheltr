# Turn-by-Turn Navigation Implementation Guide

## ✅ **Backend Implementation - COMPLETE**

### **Files Created:**

1. **`backend/navigation_directions.py`** - Turn-by-turn direction generator
   - Calculates bearings between coordinates
   - Determines turn angles and instructions
   - Generates step-by-step directions
   - Formats distances and estimated time

2. **`backend/sheltr_backend.py`** - Updated with navigation
   - Imports `generate_turn_by_turn_directions`
   - Added to `/api/calculate-route` endpoint
   - Added to `/api/nearest-safe-route` endpoint
   - Returns `directions` and `directionsSummary` in response

### **API Response Format:**

```json
{
  "route": [[14.5547, 121.0244], ...],
  "totalDistance": 3.2,
  "safetyScore": 0.85,
  "floodRisk": 0.15,
  "directions": [
    {
      "step": 1,
      "instruction": "Head North",
      "distance": 0,
      "total_distance": 0,
      "coordinates": [14.5547, 121.0244],
      "bearing": 15.5,
      "type": "start"
    },
    {
      "step": 2,
      "instruction": "Turn right",
      "distance": 150.5,
      "total_distance": 150.5,
      "coordinates": [14.5560, 121.0250],
      "bearing": 85.2,
      "turn_angle": 69.7,
      "type": "turn"
    },
    {
      "step": 3,
      "instruction": "You have arrived at your destination",
      "distance": 50.0,
      "total_distance": 3200.0,
      "coordinates": [14.5575, 121.0260],
      "bearing": 85.2,
      "type": "destination"
    }
  ],
  "directionsSummary": {
    "total_steps": 8,
    "total_distance": 3200.0,
    "total_distance_formatted": "3.2km",
    "num_turns": 6,
    "estimated_time_minutes": 38
  }
}
```

## 🔧 **Frontend Implementation - NEEDED**

### **Required Changes to `map.tsx`:**

#### **1. Add Type Definitions** (after line 36)

```typescript
type DirectionStep = {
  step: number;
  instruction: string;
  distance: number;
  total_distance: number;
  coordinates: number[];
  bearing: number;
  turn_angle?: number;
  type: 'start' | 'turn' | 'destination';
};

type DirectionsSummary = {
  total_steps: number;
  total_distance: number;
  total_distance_formatted: string;
  num_turns: number;
  estimated_time_minutes: number;
};

type RouteResult = {
  route: string[];
  totalDistance: number;
  safetyScore: number;
  floodRisk: number;
  directions?: DirectionStep[];
  directionsSummary?: DirectionsSummary;
};
```

#### **2. Add State** (after line 257)

```typescript
const [showDirections, setShowDirections] = useState(false);
```

#### **3. Add Directions Button** (after zoom controls, before closing </View>)

```typescript
{/* Directions Button */}
{routeData && routeData.directions && routeData.directions.length > 0 && (
  <Pressable 
    style={styles.directionsButton} 
    onPress={() => setShowDirections(true)}
  >
    <AppIcon name="paperplane.fill" size={20} color="#FFFFFF" />
    <ThemedText style={styles.directionsButtonText}>
      {routeData.directionsSummary?.total_steps || 0} Steps
    </ThemedText>
  </Pressable>
)}
```

#### **4. Add Directions Modal** (after Evacuation Centers Modal)

```typescript
{/* Turn-by-Turn Directions Modal */}
<Modal
  visible={showDirections}
  animationType="slide"
  presentationStyle="pageSheet"
  onRequestClose={() => setShowDirections(false)}
>
  <View style={styles.modalContainer}>
    <View style={styles.modalHeader}>
      <Pressable onPress={() => setShowDirections(false)} style={{ marginRight: 12 }}>
        <AppIcon name="chevron.left" size={24} color="#1a1a1a" />
      </Pressable>
      <ThemedText style={styles.modalTitle}>Turn-by-Turn Directions</ThemedText>
    </View>

    {routeData?.directionsSummary && (
      <View style={styles.directionsSummary}>
        <View style={styles.summaryItem}>
          <ThemedText style={styles.summaryLabel}>Distance:</ThemedText>
          <ThemedText style={styles.summaryValue}>
            {routeData.directionsSummary.total_distance_formatted}
          </ThemedText>
        </View>
        <View style={styles.summaryItem}>
          <ThemedText style={styles.summaryLabel}>Time:</ThemedText>
          <ThemedText style={styles.summaryValue}>
            {routeData.directionsSummary.estimated_time_minutes} min
          </ThemedText>
        </View>
        <View style={styles.summaryItem}>
          <ThemedText style={styles.summaryLabel}>Turns:</ThemedText>
          <ThemedText style={styles.summaryValue}>
            {routeData.directionsSummary.num_turns}
          </ThemedText>
        </View>
      </View>
    )}

    <ScrollView style={{ flex: 1 }}>
      {routeData?.directions?.map((step, index) => (
        <View key={index} style={styles.directionStep}>
          <View style={styles.stepNumber}>
            <ThemedText style={styles.stepNumberText}>{step.step}</ThemedText>
          </View>
          <View style={styles.stepContent}>
            <ThemedText style={styles.stepInstruction}>{step.instruction}</ThemedText>
            {step.distance > 0 && (
              <ThemedText style={styles.stepDistance}>
                {step.distance < 1000 
                  ? `${Math.round(step.distance)}m` 
                  : `${(step.distance / 1000).toFixed(1)}km`}
              </ThemedText>
            )}
          </View>
        </View>
      ))}
    </ScrollView>
  </View>
</Modal>
```

#### **5. Add Styles** (in StyleSheet.create)

```typescript
directionsButton: {
  position: 'absolute',
  bottom: 20,
  left: '50%',
  transform: [{ translateX: -75 }],
  flexDirection: 'row',
  alignItems: 'center',
  gap: 8,
  backgroundColor: '#0B5AA2',
  paddingVertical: 12,
  paddingHorizontal: 20,
  borderRadius: 25,
  ...SOFT_SHADOW,
},
directionsButtonText: {
  color: '#FFFFFF',
  fontSize: 16,
  fontWeight: '700',
},
directionsSummary: {
  flexDirection: 'row',
  justifyContent: 'space-around',
  padding: 16,
  backgroundColor: '#F3F4F6',
  borderBottomWidth: 1,
  borderBottomColor: '#E5E7EB',
},
summaryItem: {
  alignItems: 'center',
},
summaryLabel: {
  fontSize: 12,
  color: '#6B7280',
  marginBottom: 4,
},
summaryValue: {
  fontSize: 16,
  fontWeight: '700',
  color: '#0B5AA2',
},
directionStep: {
  flexDirection: 'row',
  padding: 16,
  borderBottomWidth: 1,
  borderBottomColor: '#F3F4F6',
},
stepNumber: {
  width: 32,
  height: 32,
  borderRadius: 16,
  backgroundColor: '#0B5AA2',
  alignItems: 'center',
  justifyContent: 'center',
  marginRight: 12,
},
stepNumberText: {
  color: '#FFFFFF',
  fontSize: 14,
  fontWeight: '700',
},
stepContent: {
  flex: 1,
},
stepInstruction: {
  fontSize: 15,
  fontWeight: '600',
  color: '#1a1a1a',
  marginBottom: 4,
},
stepDistance: {
  fontSize: 13,
  color: '#6B7280',
},
```

## 🚀 **How It Works**

### **User Flow:**

1. User selects an evacuation center
2. Route is calculated with curved roads
3. **NEW:** Backend generates turn-by-turn directions
4. **NEW:** "X Steps" button appears at bottom of map
5. **NEW:** User taps button to see step-by-step instructions
6. **NEW:** Modal shows:
   - Summary (distance, time, turns)
   - Step-by-step directions with distances
   - Clear instructions like "Turn right", "Head North"

### **Direction Types:**

- **Start:** "Head North/South/East/West"
- **Turns:**
  - "Continue straight" (< 20°)
  - "Bear slight left/right" (20-45°)
  - "Turn left/right" (45-135°)
  - "Make a sharp left/right turn" (> 135°)
- **Destination:** "You have arrived at your destination"

### **Distance Formatting:**

- < 1000m: "150m", "500m"
- ≥ 1000m: "1.5km", "3.2km"

### **Time Estimation:**

- Based on 5 km/h walking speed
- Accounts for total distance
- Displayed in minutes

## ✅ **Testing**

### **Backend Test:**

```bash
# Backend should already be running with navigation
# Check logs for: "Generated X turn-by-turn directions"
```

### **Frontend Test:**

1. Select an evacuation center
2. Wait for route to calculate
3. Look for "X Steps" button at bottom
4. Tap to see turn-by-turn directions
5. Verify:
   - Summary shows correct distance/time
   - Steps are numbered
   - Instructions are clear
   - Distances are shown for each step

## 📊 **Example Output**

**Route:** Taguig → Evacuation Center (3.2km)

**Directions:**
1. Head North
2. Turn right (150m)
3. Continue straight (500m)
4. Turn left (200m)
5. Bear slight right (300m)
6. Turn right (800m)
7. Continue straight (1.1km)
8. You have arrived at your destination (150m)

**Summary:**
- Distance: 3.2km
- Time: 38 min
- Turns: 6

---

**Status:** Backend ✅ Complete | Frontend ⏳ Needs Implementation
