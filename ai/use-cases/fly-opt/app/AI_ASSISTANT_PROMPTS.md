# Sky Routing Service - AI Assistant Sample Prompts

This document contains sample prompts for the Sky Routing Service AI Assistant. Use these examples to optimize routes for EV charging stations, deliveries, and field service operations across the UK.

---

## Table of Contents
1. [Basic Route Optimization](#basic-route-optimization)
2. [EV Charging Station Routes](#ev-charging-station-routes)
3. [Delivery & Parcel Routes](#delivery--parcel-routes)
4. [Field Service & Maintenance](#field-service--maintenance)
5. [Multi-Vehicle Distribution](#multi-vehicle-distribution)
6. [Regional UK Routes](#regional-uk-routes)
7. [Large Scale Operations](#large-scale-operations)
8. [Advanced Constraints](#advanced-constraints)

---

## Basic Route Optimization

Simple prompts to get started:

```
Optimize routes for 20 stops with 3 vehicles
```

```
Plan delivery routes for 50 locations with 5 vans
```

```
Find the best routes for 30 customer visits using 4 drivers
```

---

## EV Charging Station Routes

For EV infrastructure maintenance and inspection:

```
Optimize routes for 15 EV charging station inspections across UK with 4 service vans
```

```
Plan maintenance routes for 25 EV chargers in London area with 5 technicians
```

```
Schedule visits to 40 charging points in Manchester and Birmingham with 6 vehicles
```

```
Distribute 20 EV station inspections evenly across 4 maintenance crews in Scotland
```

```
Optimize service routes for 30 rapid chargers across South East England with 5 vans
```

---

## Delivery & Parcel Routes

For logistics and parcel delivery operations:

```
Plan routes for 100 parcel deliveries across London with 10 delivery vans
```

```
Optimize 50 next-day deliveries in Birmingham area with 5 vehicles
```

```
Schedule 80 package deliveries in Manchester with 8 drivers available 8am-6pm
```

```
Plan efficient routes for 200 parcels across Leeds and Sheffield with 15 vans
```

```
Distribute 60 express deliveries evenly across 6 couriers in Bristol
```

---

## Field Service & Maintenance

For engineer visits and service calls:

```
Schedule 40 engineer visits across Greater Manchester with 5 service vehicles
```

```
Optimize routes for 25 home installations in Edinburgh with 4 technicians
```

```
Plan 30 customer service calls in Cardiff area with 3 field engineers
```

```
Distribute 50 maintenance appointments evenly across 6 engineers in Liverpool
```

```
Schedule 35 equipment repairs across Yorkshire with 5 service vans
```

---

## Multi-Vehicle Distribution

When you want to ensure all vehicles are used:

```
Distribute 15 stops evenly across 4 service vans in UK
```

```
Spread 30 deliveries across all 5 vehicles in London
```

```
Balance 20 service calls evenly between 4 technicians in Manchester
```

```
Use all 6 vans to cover 40 locations across Birmingham
```

```
Evenly distribute 25 customer visits among 5 drivers in Scotland
```

---

## Regional UK Routes

Location-specific routing:

### London & South East
```
Optimize 50 deliveries across Central London with 5 vans
```

```
Plan routes for 30 stops in South East England with 4 vehicles
```

### Midlands
```
Schedule 40 visits across Birmingham and Coventry with 5 drivers
```

```
Optimize routes for 25 stops in East Midlands with 3 vehicles
```

### North of England
```
Plan 60 deliveries across Manchester, Leeds, and Liverpool with 8 vans
```

```
Optimize routes for 35 stops in Yorkshire with 5 vehicles
```

### Scotland
```
Schedule 30 service calls across Edinburgh and Glasgow with 4 technicians
```

```
Plan routes for 20 stops across Scotland with 3 vehicles
```

### Wales
```
Optimize 25 deliveries in Cardiff and Swansea with 3 vans
```

---

## Large Scale Operations

For high-volume routing (uses parallel processing automatically):

```
Optimize 500 deliveries across UK with 50 vehicles using parallel processing
```

```
Plan routes for 1000 stops nationwide with 80 vans using clustering
```

```
Schedule 300 service visits across England with 30 technicians, use fast processing
```

```
Distribute 800 parcels across 60 delivery drivers using parallel optimization
```

```
Large-scale route planning for 600 stops with 45 vehicles across UK
```

---

## Advanced Constraints

Prompts with specific requirements:

### Time Windows
```
Plan 40 deliveries in London with 5 vans, available 9am-5pm
```

```
Schedule 30 service calls between 8am and 6pm with 4 engineers
```

### Capacity Constraints
```
Optimize 50 deliveries with 5 trucks, each truck capacity 20 parcels
```

```
Plan routes for 30 stops with 4 vans, maximum 10 stops per van
```

### Minimize Time
```
Find fastest routes for 25 urgent deliveries with 4 vehicles
```

```
Minimize travel time for 40 service calls with 5 technicians
```

### Minimize Distance
```
Optimize 30 deliveries to minimize total distance with 4 vans
```

```
Find shortest routes for 20 stops with 3 vehicles
```

---

## Tips for Best Results

### Keywords That Trigger Special Behavior

| Keyword | Effect |
|---------|--------|
| `distribute`, `spread`, `evenly`, `balance` | Forces use of all configured vehicles |
| `parallel`, `clustering`, `fast`, `large-scale` | Enables parallel processing for large problems |
| `UK`, `London`, `Manchester`, etc. | Sets location context for UK routing |

### Recommended Format

For best results, include:
1. **Number of stops/deliveries**
2. **Number of vehicles**
3. **Location/region** (optional)
4. **Special requirements** (optional)

**Example:**
```
Optimize routes for [NUMBER] [TYPE] in [LOCATION] with [VEHICLES] vehicles
```

### Capacity Guidelines

| Stops | Vehicles | Suggested Capacity |
|-------|----------|-------------------|
| 15 | 3 | 30-40 |
| 15 | 4 | 25-30 |
| 15 | 5 | 20-25 |
| 30 | 5 | 35-45 |
| 50 | 10 | 30-40 |

---

## Troubleshooting

### "Capacity constraint violated"
- Vehicle capacity is too low for stop demands
- Solution: Let the system auto-correct or specify higher capacity

### Only 1 vehicle used when expecting more
- Total demand fits in fewer vehicles
- Solution: Use "distribute evenly" or reduce vehicle capacity

### Optimization timeout
- Problem too large for single processing
- Solution: Use "parallel processing" or "clustering" keywords

---

## Quick Reference Card

### Simple Optimization
```
Optimize [N] stops with [V] vehicles in [LOCATION]
```

### Even Distribution
```
Distribute [N] stops evenly across [V] vehicles in [LOCATION]
```

### Large Scale
```
Optimize [N] stops with [V] vehicles using parallel processing
```

### EV Stations
```
Plan routes for [N] EV charging stations with [V] service vans in UK
```

### Deliveries
```
Plan [N] deliveries across [LOCATION] with [V] vans
```

---

*Last updated: March 2026*
*Sky Routing Service - Powered by NVIDIA cuOPT*
